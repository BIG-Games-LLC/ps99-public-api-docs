# https://github.com/noemtdev

import aiohttp
from .constants import SPECIAL_POTIONS, POTION_NAMES, SPECIAL_ENCHANTS, ROMAN_NUMERALS


class Rap:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

        self.collections = []
        self.rap: list[dict] = []

    async def fetch_rap(self) -> None:
        if not self.collections:
            await self.fetch_collections()

        url = "https://biggamesapi.io/api/rap"
        async with self.session.get(url) as response:

            response_data: dict = await response.json()
            status = response.status

            if status != 200:
                response_status = response_data.get("status", "Unknown Error")
                raise Exception(
                    f"Failed to fetch RAP data. Status: {status}. Response: {response_status}")

            data = response_data.get("data", [])

            if self.rap:
                await self.clear_rap()

            for item in data:
                item_rap = await self.item_rap(item)
                if item_rap:
                    self.rap.append(item_rap)

    async def clear_rap(self) -> None:
        self.rap = []

    async def fetch_collections(self) -> None:
        url = "https://biggamesapi.io/api/collections"
        async with self.session.get(url) as response:
            response_data: dict = await response.json()
            status = response.status

            if status != 200:
                response_status = response_data.get("status", "Unknown Error")
                raise Exception(
                    f"Failed to fetch collections. Status: {status}. Response: {response_status}")

            self.collections = response_data["data"]

    # please include item names in the data 🙏
    async def item_rap(self, data: dict) -> dict:
        """
        Returns an object including the Internal ID of the Pet, it's parsed name and it's RAP value.
        Example: { "internal_id": "Huge Happy Rock", "item_name": "Shiny Rainbow Huge Happy Rock", "rap": 846111176, "category": "Pet"}
        """

        configData: dict = data.get("configData", None)
        if not configData:
            return None

        category = data.get("category", "")
        rap = data.get("value", 0)
        item_id = configData.get("id", "Unknown Item")

        if category in ["Hoverboard", "Charm", "Booth", "Box"]:
            item_name = f"{item_id} {category}"
            return {"internal_id": item_id, "item_name": item_name, "rap": rap, "category": category}

        elif category in ["Fruit", "Misc", "Egg", "Lootbox", "Ultimate"]:
            return {"internal_id": item_id, "item_name": item_id, "rap": rap, "category": category}

        elif category == "Pet":

            pet_tier_string = " "
            pet_tier = configData.get("pt", 0)

            if pet_tier == 1:
                pet_tier_string = " Golden "

            elif pet_tier == 2:
                pet_tier_string = " Rainbow "

            shiny = configData.get("sh", False)

            shiny_string = ""
            if shiny is True:
                shiny_string = "Shiny"

            pet_name = f"{shiny_string}{pet_tier_string}{item_id}".strip()

            return {"internal_id": item_id, "item_name": pet_name, "rap": rap, "category": category}

        elif category == "XPPotion":

            potion_name = f"{item_id} XP Potion"
            return {"internal_id": item_id, "item_name": potion_name, "rap": rap, "category": category}

        elif category == "Potion":

            if item_id in SPECIAL_POTIONS:
                return {"internal_id": item_id, "item_name": SPECIAL_POTIONS[item_id], "rap": rap, "category": category}

            potion_tier = configData.get("tn", 1)

            numeral = "?"
            if potion_tier in ROMAN_NUMERALS:
                numeral = ROMAN_NUMERALS[potion_tier]

            potion_name = item_id
            if item_id in POTION_NAMES:
                potion_name = POTION_NAMES[item_id]

            final_potion_name = f"{potion_name} Potion {numeral}".strip()

            return {"internal_id": item_id, "item_name": final_potion_name, "rap": rap, "category": category}

        elif category == "Enchant":

            if item_id in SPECIAL_ENCHANTS:
                return {"internal_id": item_id, "item_name": SPECIAL_ENCHANTS[item_id], "rap": rap, "category": category}

            enchant_tier = configData.get("tn", 1)

            numeral = "?"
            if enchant_tier in ROMAN_NUMERALS:
                numeral = ROMAN_NUMERALS[enchant_tier]

            enchant_name = f"{item_id} {numeral}".strip()
            return {"internal_id": item_id, "item_name": enchant_name, "rap": rap, "category": category}

        elif category == "Seed":
            seed_name = f"{item_id} Plant Seed"
            return {"internal_id": item_id, "item_name": seed_name, "rap": rap, "category": category}
