"""
Telegram Account Manager - Country Detection Utility

Automatically detects country from phone number using libphonenumber.
Supports hiding empty categories by tracking countries with actual accounts.
"""

from typing import Optional

from phonenumbers import PhoneNumberFormat
from phonenumbers import carrier
from phonenumbers import geocoder
from phonenumbers import NumberParseException
from phonenumbers import PhoneNumber
from phonenumbers import number_type


class CountryDetector:
    """
    Phone number country detection with country code mapping.
    
    Features:
    - Extract country code and national number
    - Get country name from phone number
    - Support for hidden empty categories
    - Country name translations (optional)
    """
    
    # Canadian area codes for distinguishing Canada from US (both use +1)
    CANADIAN_AREA_CODES = frozenset({
        "204", "226", "236", "249", "250", "257", "289", "306", "343", "365",
        "368", "403", "416", "418", "428", "431", "437", "438", "450", "468",
        "474", "506", "514", "519", "548", "579", "581", "587", "604", "613",
        "639", "647", "672", "683", "705", "709", "742", "778", "780", "782",
        "807", "819", "825", "867", "873", "902", "905"
    })
    
    # Common country code mappings for quick reference
    COUNTRY_CODES = {
        "+1": "North America (+1)",  # Special: distinguishes US/Canada by area code
        "+7": "Russia",
        "+20": "Egypt",
        "+27": "South Africa",
        "+30": "Greece",
        "+31": "Netherlands",
        "+32": "Belgium",
        "+33": "France",
        "+34": "Spain",
        "+36": "Hungary",
        "+39": "Italy",
        "+40": "Romania",
        "+41": "Switzerland",
        "+43": "Austria",
        "+44": "United Kingdom",
        "+45": "Denmark",
        "+46": "Sweden",
        "+47": "Norway",
        "+48": "Poland",
        "+49": "Germany",
        "+51": "Peru",
        "+52": "Mexico",
        "+54": "Argentina",
        "+55": "Brazil",
        "+56": "Chile",
        "+57": "Colombia",
        "+58": "Venezuela",
        "+60": "Malaysia",
        "+61": "Australia",
        "+62": "Indonesia",
        "+63": "Philippines",
        "+64": "New Zealand",
        "+65": "Singapore",
        "+66": "Thailand",
        "+81": "Japan",
        "+82": "South Korea",
        "+84": "Vietnam",
        "+86": "China",
        "+90": "Turkey",
        "+91": "India",
        "+92": "Pakistan",
        "+93": "Afghanistan",
        "+94": "Sri Lanka",
        "+95": "Myanmar",
        "+98": "Iran",
        "+211": "South Sudan",
        "+212": "Morocco",
        "+213": "Algeria",
        "+216": "Tunisia",
        "+218": "Libya",
        "+220": "Gambia",
        "+221": "Senegal",
        "+222": "Mauritania",
        "+223": "Mali",
        "+224": "Guinea",
        "+225": "Ivory Coast",
        "+226": "Burkina Faso",
        "+227": "Niger",
        "+228": "Togo",
        "+229": "Benin",
        "+230": "Mauritius",
        "+231": "Liberia",
        "+232": "Sierra Leone",
        "+233": "Ghana",
        "+234": "Nigeria",
        "+235": "Chad",
        "+236": "Central African Republic",
        "+237": "Cameroon",
        "+238": "Cape Verde",
        "+239": "São Tomé and Príncipe",
        "+240": "Equatorial Guinea",
        "+241": "Gabon",
        "+242": "Republic of the Congo",
        "+243": "Democratic Republic of the Congo",
        "+244": "Angola",
        "+245": "Guinea-Bissau",
        "+246": "British Indian Ocean Territory",
        "+247": "Ascension Island",
        "+248": "Seychelles",
        "+249": "Sudan",
        "+250": "Rwanda",
        "+251": "Ethiopia",
        "+252": "Somalia",
        "+253": "Djibouti",
        "+254": "Kenya",
        "+255": "Tanzania",
        "+256": "Uganda",
        "+257": "Burundi",
        "+258": "Mozambique",
        "+260": "Zambia",
        "+261": "Madagascar",
        "+262": "Mayotte",
        "+263": "Zimbabwe",
        "+264": "Namibia",
        "+265": "Malawi",
        "+266": "Lesotho",
        "+267": "Eswatini",
        "+268": "Eswatini",
        "+269": "Comoros",
        "+290": "Saint Helena",
        "+291": "Eritrea",
        "+297": "Aruba",
        "+298": "Faroe Islands",
        "+299": "Greenland",
        "+350": "Gibraltar",
        "+351": "Portugal",
        "+352": "Luxembourg",
        "+353": "Ireland",
        "+354": "Iceland",
        "+355": "Albania",
        "+356": "Malta",
        "+357": "Cyprus",
        "+358": "Finland",
        "+359": "Bulgaria",
        "+370": "Lithuania",
        "+371": "Latvia",
        "+372": "Estonia",
        "+373": "Moldova",
        "+374": "Armenia",
        "+375": "Belarus",
        "+376": "Andorra",
        "+377": "Monaco",
        "+378": "San Marino",
        "+379": "Vatican City",
        "+380": "Ukraine",
        "+381": "Serbia",
        "+382": "Montenegro",
        "+383": "Kosovo",
        "+385": "Croatia",
        "+386": "Slovenia",
        "+387": "Bosnia and Herzegovina",
        "+389": "North Macedonia",
        "+420": "Czech Republic",
        "+421": "Slovakia",
        "+423": "Liechtenstein",
        "+500": "Falkland Islands",
        "+501": "Belize",
        "+502": "Guatemala",
        "+503": "El Salvador",
        "+504": "Honduras",
        "+505": "Nicaragua",
        "+506": "Costa Rica",
        "+507": "Panama",
        "+508": "Saint Pierre and Miquelon",
        "+509": "Haiti",
        "+590": "Guadeloupe",
        "+591": "Bolivia",
        "+592": "Guyana",
        "+593": "Ecuador",
        "+594": "French Guiana",
        "+595": "Paraguay",
        "+596": "Martinique",
        "+597": "Suriname",
        "+598": "Uruguay",
        "+599": "Curaçao",
        "+670": "East Timor",
        "+672": "Norfolk Island",
        "+673": "Brunei",
        "+674": "Nauru",
        "+675": "Papua New Guinea",
        "+676": "Tonga",
        "+677": "Solomon Islands",
        "+678": "Vanuatu",
        "+679": "Fiji",
        "+680": "Palau",
        "+681": "Wallis and Futuna",
        "+682": "Cook Islands",
        "+683": "Niue",
        "+684": "American Samoa",
        "+685": "Samoa",
        "+686": "Kiribati",
        "+687": "New Caledonia",
        "+688": "Tuvalu",
        "+689": "French Polynesia",
        "+690": "Tokelau",
        "+691": "Micronesia",
        "+692": "Marshall Islands",
        "+850": "North Korea",
        "+852": "Hong Kong",
        "+853": "Macau",
        "+855": "Cambodia",
        "+856": "Laos",
        "+880": "Bangladesh",
        "+886": "Taiwan",
        "+960": "Maldives",
        "+961": "Lebanon",
        "+962": "Jordan",
        "+963": "Syria",
        "+964": "Iraq",
        "+965": "Kuwait",
        "+966": "Saudi Arabia",
        "+967": "Yemen",
        "+968": "Oman",
        "+970": "Palestine",
        "+971": "United Arab Emirates",
        "+972": "Israel",
        "+973": "Bahrain",
        "+974": "Qatar",
        "+975": "Bhutan",
        "+976": "Mongolia",
        "+977": "Nepal",
        "+992": "Tajikistan",
        "+993": "Turkmenistan",
        "+994": "Azerbaijan",
        "+995": "Georgia",
        "+996": "Kyrgyzstan",
        "+998": "Uzbekistan",
    }
    
    # Emoji mapping for countries
    COUNTRY_EMOJIS = {
        "United States": "🇺🇸",
        "Canada": "🇨🇦",
        "Russia": "🇷🇺",
        "United Kingdom": "🇬🇧",
        "Germany": "🇩🇪",
        "France": "🇫🇷",
        "China": "🇨🇳",
        "India": "🇮🇳",
        "Japan": "🇯🇵",
        "Australia": "🇦🇺",
        "Brazil": "🇧🇷",
        "Iran": "🇮🇷",
        "Turkey": "🇹🇷",
        "Indonesia": "🇮🇩",
        "Pakistan": "🇵🇰",
        "Nigeria": "🇳🇬",
        "Mexico": "🇲🇽",
        "Saudi Arabia": "🇸🇦",
        "South Korea": "🇰🇷",
        "South Africa": "🇿🇦",
        "Thailand": "🇹🇭",
        "Vietnam": "🇻🇳",
        "Malaysia": "🇲🇾",
        "Philippines": "🇵🇭",
        "Egypt": "🇪🇬",
        "Israel": "🇮🇱",
        "United Arab Emirates": "🇦🇪",
    }
    
    def __init__(self, language: str = "en"):
        """
        Initialize the country detector.
        
        Args:
            language: Language for country name translation (default: English)
        """
        self.language = language
    
    def detect(self, phone_number: str) -> dict:
        """
        Detect country from phone number.
        
        Args:
            phone_number: Phone number with country code (e.g., +1, +98)
            
        Returns:
            Dictionary with country information:
            {
                "country_code": "+1",
                "country_name": "United States",
                "national_number": "5551234567",
                "is_valid": True/False,
                "emoji": "🇺🇸",
                "region_code": "US"
            }
        """
        # Clean the phone number
        clean_number = phone_number.strip().replace(" ", "").replace("-", "")
        
        # Add + if not present
        if not clean_number.startswith("+"):
            clean_number = "+" + clean_number
        
        try:
            # Parse the phone number
            parsed: PhoneNumber = carrier.phone_number_object(clean_number)
            
            # Extract country code and national number
            country_code = f"+{parsed.country_code}"
            national_number = str(parsed.national_number)
            
            # Special handling for +1 (US and Canada)
            if country_code == "+1":
                # Extract area code (first 3 digits of national number)
                area_code = national_number[:3] if len(national_number) >= 3 else ""
                if area_code in self.CANADIAN_AREA_CODES:
                    country_name = "Canada"
                else:
                    country_name = "United States"
            else:
                # Get country name from libphonenumber
                country_name = geocoder.description_for_number(
                    parsed, 
                    self.language
                )
                
                # Fallback to our mapping if libphonenumber doesn't have it
                if not country_name or country_name == "Unknown":
                    country_name = self.COUNTRY_CODES.get(
                        country_code, 
                        f"Unknown ({country_code})"
                    )
            
            # Get region code
            region_code = geocoder.region_code_for_number(parsed)
            
            # Determine if it's a mobile or fixed line
            phone_type = number_type(parsed)
            # number_type returns: 0=FIXED_LINE, 1=MOBILE, 2=FIXED_LINE_OR_MOBILE
            is_mobile = phone_type in (1, 2)
            
            return {
                "country_code": country_code,
                "country_name": country_name,
                "national_number": national_number,
                "is_valid": True,
                "emoji": self.COUNTRY_EMOJIS.get(country_name, "🌍"),
                "region_code": region_code,
                "is_mobile": is_mobile,
                "formatted": self.format_number(parsed),
            }
            
        except NumberParseException:
            # Return invalid result
            return {
                "country_code": "",
                "country_name": "Unknown",
                "national_number": "",
                "is_valid": False,
                "emoji": "🌍",
                "region_code": "",
                "is_mobile": False,
                "formatted": phone_number,
            }
    
    def format_number(self, phone: PhoneNumber) -> str:
        """
        Format phone number in international format.
        
        Args:
            phone: Parsed PhoneNumber object
            
        Returns:
            Formatted phone number string
        """
        return carrier.format_number(
            phone, 
            PhoneNumberFormat.INTERNATIONAL
        )
    
    def get_country_emoji(self, country_code: str) -> str:
        """
        Get emoji for a country code.
        
        Args:
            country_code: Country code (e.g., "+1", "+98")
            
        Returns:
            Country emoji or default globe emoji
        """
        country_name = self.COUNTRY_CODES.get(country_code, "")
        return self.COUNTRY_EMOJIS.get(country_name, "🌍")
    
    def validate_number(self, phone_number: str) -> bool:
        """
        Validate a phone number.
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        result = self.detect(phone_number)
        return result["is_valid"]


# Singleton instance
_country_detector: Optional[CountryDetector] = None


def get_country_detector(language: str = "en") -> CountryDetector:
    """
    Get the country detector singleton instance.
    
    Args:
        language: Language for country names
        
    Returns:
        CountryDetector instance
    """
    global _country_detector
    if _country_detector is None:
        _country_detector = CountryDetector(language)
    return _country_detector


def get_country_info(phone_number: str) -> dict:
    """
    Convenience function to get country info from a phone number.
    
    Args:
        phone_number: Phone number with country code
        
    Returns:
        Country information dictionary
    """
    detector = get_country_detector()
    return detector.detect(phone_number)
