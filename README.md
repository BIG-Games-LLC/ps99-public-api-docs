## Table of Contents

- [Introduction](#introduction)
- [API Endpoints](#api-endpoints)
  - [Collections](#get-collections)
  - [Collection](#get-collection)
  - [Clans List](#get-clans-list)
  - [Clans Total](#get-clans-total)
  - [Clans](#get-clans)
  - [Clan](#get-clan)
  - [Exists](#get-exists)
  - [RAP](#get-rap)
  - [Active Clan Battle](#get-active-clan-battle)
  - [Image](#get-image)
- [API Information](#api-information)
  - [Standard Responses](#standard-responses)
  - [Caching Policy](#caching-policy)
  - [Rate Limiting](#rate-limiting)
  - [Versioning](#versioning)
- [Code Examples](#code-examples)
- [Contact](#contact-information)

## Introduction

The Pet Simulator 99 Public API provides access to in-game data and configuration details. With this API, developers can retrieve information about pets, items, clans, and more, allowing for the creation of external tools, websites, Discord bots, and other applications.

## API Endpoints

Production URL: https://ps99.biggamesapi.io/

## GET Collections
`https://ps99.biggamesapi.io/api/collections`

Types of data from Pet Simulator 99's in-game configuration files. Each of these may be queried. These are like tables of a database.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/collections'
```

**Example Response**
```json
{
    "status": "ok",
    "data": [
        "Achievements",
        "Boosts",
        "Booths",
        "Boxes",
        "Buffs",
        "Charms",
        "Currency",
        "Eggs",
        "Enchants",
        "FishingRods",
        "Fruits",
        "GuildBattles",
        "Hoverboards",
        "Lootboxes",
        "Mastery",
        "MiscItems",
        "Pets",
        "Potions",
        "RandomEvents",
        "Ranks",
        "Rarity",
        "Rebirths",
        "SecretRooms",
        "Seeds",
        "Shovels",
        "Sprinklers",
        "Ultimates",
        "Upgrades",
        "WateringCans",
        "Worlds",
        "ZoneFlags",
        "Zones",
        "Merchants",
        "XPPotions"
    ]
}
```

## GET Collection
`https://ps99.biggamesapi.io/api/collection/{collectionName}`

The details from the specified collection. This contains a list of configuration data from the game configuration files. These are like rows of a database.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/collection/Pets'
```

**Example Response**
```json
{
    "status": "ok",
    "data": [
        {
            "configName": "Huge Cosmic Axolotl",
            "category": "Huge",
            "configData": {
                "goldenThumbnail": "",
                "indexObtainable": true,
                "huge": true,
                "name": "Huge Cosmic Axolotl",
                "indexDesc": "Found in the Exclusive Cosmic Egg!",
                "thumbnail": "rbxassetid://15201636161"
            },
            "dateCreated": null,
            "dateModified": null,
            "hash": null,
            "collection": "Pets"
        }
    ]
}
```

## GET Clans List
`https://ps99.biggamesapi.io/api/clansList`

Get a list of all clan names.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/clansList'
```

**Example Response**
```json
{
    "status": "ok",
    "data": [
        "KIL1",
        "ukbd",
        "c1aw",
        "hdkn",
        "C0ME",
        "Lqwe",
        "Eswp",
        "3987",
        "TBHE",
        "hffc",
        "YMCY",
        "KHSH",
        "40z",
        "BWFL",
        "RNC",
        "jlc9",
        "LGSW",
        "vjnh",
        "wwkp",
        "Nvyy"
    ]
}
```

## GET Clans Total
`https://ps99.biggamesapi.io/api/clansTotal`

Get the total number of clans.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/clansTotal'
```

**Example Response**
```json
{
    "status": "ok",
    "data": 145463
}
```

## GET Clans
`https://ps99.biggamesapi.io/api/clans`

Get paginated list of clans with sorting options.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `pageSize` (optional): Number of items per page (default: 10)
- `sort` (optional): Field to sort by (default: Points)
- `sortOrder` (optional): Sort order - "asc" or "desc" (default: desc)

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/clans?page=1&pageSize=10&sort=Points&sortOrder=desc'
```

**Example Response**
```json
{
    "status": "ok",
    "data": [
        {
            "Created": 1701469087,
            "Name": "Goop",
            "Icon": "rbxassetid://14976584980",
            "MemberCapacity": 75,
            "DepositedDiamonds": 13680537760,
            "CountryCode": "US",
            "Members": 71,
            "Points": 17710501
        },
        {
            "Created": 1702641421,
            "Name": "fr3e",
            "Icon": "rbxassetid://17709274952",
            "MemberCapacity": 75,
            "DepositedDiamonds": 22603773968,
            "CountryCode": "NZ",
            "Members": 66,
            "Points": 17085509
        }
    ]
}
```

## GET Clan
`https://ps99.biggamesapi.io/api/clan/{clanName}`

Get details for a specific clan.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/clan/CAT'
```

**Example Response**
```json
{
    "status": "ok",
    "data": {
        "Created": 1701455468,
        "Owner": 2905240521,
        "Name": "CAT",
        "Icon": "rbxassetid://14976576332",
        "Desc": "CATTTTT",
        "MemberCapacity": 75,
        "OfficerCapacity": 10,
        "GuildLevel": 7,
        "Members": [
            {
                "UserID": 140258990,
                "PermissionLevel": 90,
                "JoinTime": 1701738298
            }
        ],
        "Contribution": {
            "Battle": [
                {
                    "UserID": 4168075450,
                    "Points": 50000000
                }
            ]
        },
        "CountryCode": "HK",
        "BronzeMedals": 4,
        "LastKickTimestamp": 1724297807,
        "SilverMedals": 1,
        "GoldMedals": 6
    }
}
```

## GET Exists
`https://ps99.biggamesapi.io/api/exists`

Exists data for each item and pet in the game.

- **For pets:** pt=1 is golden, pt=2 is rainbow, sh is shiny
- **For potions:** enchants, etc: tn is tier number

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/exists'
```

**Example Response**
```json
{
    "status": "ok",
    "data": [
        {
            "category": "Pet",
            "configData": {
                "id": "Unicorn Dragon"
            },
            "value": 816593
        },
        {
            "category": "Pet",
            "configData": {
                "id": "Turtle"
            },
            "value": 189401576
        },
        {
            "category": "Pet",
            "configData": {
                "id": "Scarecrow Cat",
                "pt": 1
            },
            "value": 31908237
        }
    ]
}
```

## GET RAP
`https://ps99.biggamesapi.io/api/rap`

Get RAP (Recent Average Price) data for items.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/rap'
```

**Example Response**
```json
{
    "status": "ok",
    "data": [
        {
            "category": "XPPotion",
            "configData": {
                "id": "Huge"
            },
            "value": 1456980
        },
        {
            "category": "XPPotion",
            "configData": {
                "id": "Ultimate"
            },
            "value": 235535
        },
        {
            "category": "XPPotion",
            "configData": {
                "id": "Titanic"
            },
            "value": 29002
        }
    ]
}
```

## GET Active Clan Battle
`https://ps99.biggamesapi.io/api/activeClanBattle`

Get information about the currently active clan battle.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/api/activeClanBattle'
```

**Example Response**
```json
{
    "status": "ok",
    "data": {
        "_id": "66eef7ceb499860269653f4b",
        "configName": "CatchingBattle",
        "category": "GuildBattles",
        "configData": {
            "PlacementRewards": [
                {
                    "Item": {
                        "_data": {
                            "id": "Clan Gift"
                        }
                    },
                    "Best": 1,
                    "Worst": 500
                }
            ]
        }
    }
}
```

## GET Image
`https://ps99.biggamesapi.io/image/{imageId}`

Displays a Roblox library asset as an image by proxying the request.

**Example Request**
```curl
curl --location 'https://ps99.biggamesapi.io/image/14615650278'
```

**Example Response**
Returns the image file directly (binary data).

## API Information

### Standard Responses
The API follows a standard response format for successful and error responses:
- **Successful Response**: Returns a status code of 200 with JSON data containing a 'status' field set to 'ok' and optional 'data' field with the response message.
- **Error Response**: Returns a status code of 400 with JSON data containing a 'status' field set to 'error' and an 'error' field containing an error message. Additionally, an 'ignore' flag is included to indicate that the error can be safely ignored.

### Caching Policy
Data from the API is cached for 60 seconds, except for Recent Average Price (RAP) data, which is cached for 4 hours.

### Rate Limiting
We encourage users to avoid spamming the API with excessive requests. Please cache your requests and limit requests to 100 per minute per IP address.

### Versioning
We strive to maintain backward compatibility with all API versions. Any changes that may affect existing integrations will be clearly documented in the changelog.

## Contact Information
For any inquiries, feedback, or support requests related to the Pet Simulator 99 Public API, please open an issue on the [GitHub repository](https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues).

## Code Examples

### JavaScript Example:
```javascript
// Example using Fetch API in JavaScript
fetch('https://ps99.biggamesapi.io/api/collections')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

### Python Example:
```python
# Example using requests library in Python
import requests

response = requests.get('https://ps99.biggamesapi.io/api/collections')
data = response.json()
print(data)
```

### PHP Example:
```php
<?php
// Example using cURL in PHP
$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://ps99.biggamesapi.io/api/collections',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => true,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'GET',
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
?>
```

Explore the endpoints and integrate them into your applications! Happy coding!