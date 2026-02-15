import sys
import os
import json
import re
import time
import requests
from datetime import date
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# MCP-internal imports (no backend dependencies)
from utils.logger import setup_logger
from utils.exception import MCPException
from prompts import SEARCH_PARAMS_PROMPT, RANK_FLIGHTS_PROMPT

load_dotenv()

logger = setup_logger(name="mcp_search_agent")


def extract_json_from_response(text: str) -> str:
    """
    Extract JSON from LLM response that may be wrapped in markdown code blocks.
    Handles responses like:
      ```json\n{...}\n```
      ```\n{...}\n```
      or plain JSON
    """
    # Try to extract from markdown code fences
    pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Try to find raw JSON object or array
    text = text.strip()
    if text.startswith('{') or text.startswith('['):
        return text
    
    # Last resort: find first { to last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end + 1]
    
    return text


class ResearchAgent:
    """
    Research Agent:
    1. Extracts structured flight search parameters using LLM
    2. Calls Amadeus Flight Offers API
    3. Ranks results using LLM
    """

    def __init__(self, llm):
        self.llm = llm
        self.token = None
        self.token_expiry = 0

    def get_access_token(self):
        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"

            data = {
                "grant_type": "client_credentials",
                "client_id": os.getenv("Amadeus_API_Key"),
                "client_secret": os.getenv("Amadeus_API_Secret")
            }

            response = requests.post(url, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.token = token_data["access_token"]
            self.token_expiry = time.time() + token_data["expires_in"]

            logger.info("Amadeus token generated successfully")

        except Exception as e:
            logger.error("Failed to generate Amadeus token")
            raise MCPException(e, sys)

    def ensure_token(self):
        if not self.token or time.time() >= self.token_expiry:
            self.get_access_token()



    def extract_search_params(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to extract structured flight search parameters from state.
        """

        prompt = SEARCH_PARAMS_PROMPT.format(state=state, today=date.today().isoformat())

        try:
            response = self.llm.invoke(prompt)

            # If using OpenAI-style response object
            content = response.content if hasattr(response, "content") else response
            logger.info(f"LLM raw response: {content}")

            # Extract JSON from potential markdown wrapping
            clean_json = extract_json_from_response(content)
            return json.loads(clean_json)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {content}")
            raise MCPException(e, sys)
        except Exception as e:
            logger.error("LLM failed to extract search parameters")
            raise MCPException(e, sys)


    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        max_results: int = 5,
    ) -> Dict[str, Any]:

        try:
            self.ensure_token()

            url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date,
                "adults": adults,
                "max": max_results,
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error("Flight search failed")
            raise MCPException(e, sys)


    def rank_flights(self, flights: List[Dict], state: Dict[str, Any]):

        if not flights:
            return []

        prompt = RANK_FLIGHTS_PROMPT.format(state=state, flights=flights)

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else response
            logger.info(f"LLM ranking raw response: {content}")

            # Extract JSON from potential markdown wrapping
            clean_json = extract_json_from_response(content)
            ranked = json.loads(clean_json)

            # Ensure it's a list
            if isinstance(ranked, list):
                return ranked
            logger.warning("LLM ranking did not return a list, using original offers")
            return flights

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"LLM ranking failed ({e}), returning original offers")
            # Return original flight offers instead of crashing
            return flights


    def research(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration method (LangGraph node):
        1. Extract params via LLM
        2. Call flight API
        3. Rank flights
        4. Return state update with results
        """

        try:
            logger.info("Research agent started")

            # 1️⃣ Extract parameters
            search_params = self.extract_search_params(state)
            logger.info(f"Extracted search params: {search_params}")

            # 2️⃣ Validate required params before calling API
            origin = search_params.get("origin", "").strip()
            destination = search_params.get("destination", "").strip()
            departure_date = search_params.get("departure_date", "").strip()

            missing = []
            if not origin:
                missing.append("departure city")
            if not destination:
                missing.append("destination city")
            if not departure_date:
                missing.append("travel date")

            if missing:
                missing_str = ", ".join(missing)
                logger.warning(f"Missing required params: {missing_str}")
                return {
                    "search_params": search_params,
                    "ranked_flights": [],
                    "response": f"I need a few more details to search flights. "
                                f"Please provide: {missing_str}.",
                }

            # 3️⃣ Call Amadeus
            flight_data = self.search_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                adults=search_params.get("adults", 1),
                max_results=search_params.get("max_results", 5),
            )

            offers = flight_data.get("data", [])
            logger.info(f"Found {len(offers)} flight offers")

            # 3.5️⃣ Convert EUR prices to INR
            EUR_TO_INR = 107.37
            for offer in offers:
                if "price" in offer:
                    try:
                        eur_total = float(offer["price"].get("total", 0))
                        offer["price"]["total"] = str(round(eur_total * EUR_TO_INR, 2))
                        offer["price"]["currency"] = "INR"

                        if "grandTotal" in offer["price"]:
                            eur_grand = float(offer["price"]["grandTotal"])
                            offer["price"]["grandTotal"] = str(round(eur_grand * EUR_TO_INR, 2))
                    except (ValueError, TypeError):
                        pass

            # 4️⃣ Rank flights
            ranked_flights = self.rank_flights(offers, state)

            # 5️⃣ Return state update for LangGraph
            return {
                "search_params": search_params,
                "ranked_flights": ranked_flights,
            }

        except Exception as e:
            logger.error(f"Research agent failed: {e}")
            return {
                "search_params": {},
                "ranked_flights": [],
                "response": "Sorry, I encountered an error while searching for flights. "
                            "Please try again with your travel details.",
            }


