from pymongo import MongoClient
from typing import Dict, List, Optional
from bson import ObjectId
import os

class MenuFetcher:
    def __init__(self):
        """
        Inizializza il client MongoDB e le collezioni necessarie.
        """
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client[os.getenv("DATABASE_NAME")]
        self.categories_collection = self.db["categories"]  # Collezione delle categorie
        self.menu_variants_collection = self.db["menu_variants"]  # Collezione delle varianti del menu
        self.users_collection = self.db["users"]  # Collezione degli utenti (merchant)

    def get_menu(self, merchant_id: str) -> List[Dict]:
        """
        Recupera il menu in base a MerchantID, gestendo le varianti.
        :param merchant_id: ID del merchant.
        :return: Lista di menu (uno per variante o un singolo menu se non ci sono varianti).
        """
        # Recupera le categorie del merchant
        categories = self.get_categories_for_menu_by_user_id(merchant_id)

        if not categories:
            return []

        # Recupera le varianti del menu
        menu_variants = self.get_variants_list(merchant_id)

        # Trova le varianti dalle categorie
        variants_from_categories = self.get_variants_from_categories(categories, menu_variants)

        # Gestione delle varianti
        if len(variants_from_categories) >= 2:
            # Restituisci un menu per ogni variante
            return [
                self.build_menu_for_variant(categories, variant)
                for variant in variants_from_categories
            ]
        elif len(variants_from_categories) == 1:
            # Restituisci due menu: uno per la variante e uno per i piatti senza varianti
            variant = variants_from_categories[0]
            other_variant = self.get_other_variant(menu_variants, variants_from_categories)
            return [
                self.build_menu_for_variant(categories, variant),
                self.build_menu_for_other_variant(categories, other_variant)
            ]
        else:
            # Restituisci un singolo menu senza varianti
            return [self.build_default_menu(categories)]

    def get_categories_for_menu_by_user_id(self, merchant_id: str) -> List[Dict]:
        """
        Recupera le categorie per il menu in base a MerchantID.
        :param merchant_id: ID del merchant.
        :return: Lista di categorie.
        """
        user = self.users_collection.find_one({"_id": ObjectId(merchant_id)})

        if not user:
            return []

        category_ids = user.get("merchantInfo", {}).get("categories", [])

        return self.get_categories_for_menu(category_ids)

    def get_categories_for_menu(self, category_ids: List[str]) -> List[Dict]:
        """
        Recupera le categorie per il menu in base agli ID delle categorie.
        :param category_ids: Lista di ID delle categorie.
        :return: Lista di categorie.
        """
        if not category_ids:
            return []

        # Recupera le categorie dal database
        categories = self.categories_collection.find({"_id": {"$in": [ObjectId(id) for id in category_ids]}})
        return list(categories)

    def get_variants_list(self, merchant_id: str) -> List[Dict]:
        """
        Recupera le varianti del menu in base a MerchantID.
        :param merchant_id: ID del merchant.
        :return: Lista di varianti.
        """
        if not merchant_id:
            return []

        return list(self.menu_variants_collection.find({"merchantID": merchant_id}))

    def get_variants_from_categories(self, categories: List[Dict], menu_variants: List[Dict]) -> List[Dict]:
        """
        Estrae le varianti dalle categorie e dagli item.
        :param categories: Lista di categorie.
        :param menu_variants: Lista di varianti del menu.
        :return: Lista di varianti.
        """
        variants = []
        for category in categories:
            if category.get("variants"):
                variants.extend(category["variants"])
            for item in category.get("items", []):
                if item.get("variants"):
                    variants.extend(item["variants"])

        # Filtra e mappa le varianti
        return [
            next((mv for mv in menu_variants if mv["id"] == variant["id"]), None)
            for variant in variants
            if variant
        ]

    def get_other_variant(self, menu_variants: List[Dict], variants_from_categories: List[Dict]) -> Dict:
        """
        Trova la variante "Altro" (piatti senza varianti).
        :param menu_variants: Lista di varianti del menu.
        :param variants_from_categories: Lista di varianti dalle categorie.
        :return: Variante "Altro".
        """
        variants_list = [mv for mv in menu_variants if not any(v["id"] == mv["id"] for v in variants_from_categories)]
        return variants_list[0] if variants_list else {"id": "other", "name": "Altro"}

    def build_menu_for_variant(self, categories: List[Dict], variant: Dict) -> Dict:
        """
        Costruisce il menu per una specifica variante.
        :param categories: Lista di categorie.
        :param variant: Variante selezionata.
        :return: Dati del menu per la variante.
        """
        return {
            "id": variant["id"],
            "name": variant["name"],
            "image": variant.get("image"),
            "description": variant.get("description"),
            "categories": [
                {
                    **category,
                    "items": [
                        item for item in category.get("items", [])
                        if not item.get("variants") or any(v["id"] == variant["id"] for v in item["variants"])
                    ]
                }
                for category in categories
                if not category.get("variants") or any(v["id"] == variant["id"] for v in category["variants"])
            ]
        }

    def build_menu_for_other_variant(self, categories: List[Dict], other_variant: Dict) -> Dict:
        """
        Costruisce il menu per la variante "Altro" (piatti senza varianti).
        :param categories: Lista di categorie.
        :param other_variant: Variante "Altro".
        :return: Dati del menu per la variante "Altro".
        """
        return {
            "id": other_variant["id"],
            "name": other_variant["name"],
            "image": other_variant.get("image"),
            "description": other_variant.get("description"),
            "categories": [
                {
                    **category,
                    "items": [
                        item for item in category.get("items", [])
                        if not item.get("variants") or len(item["variants"]) == 0
                    ]
                }
                for category in categories
                if not category.get("variants") or len(category["variants"]) == 0
            ]
        }

    def build_default_menu(self, categories: List[Dict]) -> Dict:
        """
        Costruisce il menu predefinito (senza varianti).
        :param categories: Lista di categorie.
        :return: Dati del menu.
        """
        return {
            "id": "menu",
            "name": "Menu",
            "categories": categories
        }
