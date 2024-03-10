## Introduction

The Pet Simulator 99 Public API provides access to in-game data and configuration details. With this API, developers can retrieve information about pets, items, clans, and more, allowing for the creation of external tools, websites, Discord bots, and other applications.

## Usage Documentation

Below are the endpoints available in the Pet Simulator 99 Public API along with their descriptions and usage instructions:

https://docs.biggamesapi.io/

## Examples of Usage

### JavaScript Example:
```javascript
// Example using Fetch API in JavaScript
fetch('https://biggamesapi.io/api/collections')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

### Python Example:
```python
# Example using requests library in Python
import requests

response = requests.get('https://biggamesapi.io/api/collections')
data = response.json()
print(data)
```

### PHP Example:
```php
<?php
// Example using cURL in PHP
$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://biggamesapi.io/api/collections',
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

## Authentication:
Authentication is not required to access the Pet Simulator 99 Public API. You can start using the API right away without the need for any authentication credentials.

## Rate Limiting:
We encourage users to avoid spamming the API with excessive requests. Please cache your requests and limit requests to 100 per minute per IP address.

## Standard Responses:
The API follows a standard response format for successful and error responses:
- **Successful Response**: Returns a status code of 200 with JSON data containing a 'status' field set to 'ok' and optional 'data' field with the response message.
- **Error Response**: Returns a JSON object with a 'status' field set to 'error' and an 'error' field containing an error message. Additionally, an 'ignore' flag is included to indicate that the error can be safely ignored.

## Versioning:
We strive to maintain backward compatibility with all API versions. Any changes that may affect existing integrations will be clearly documented in the changelog.

## Contact Information:
For any inquiries, feedback, or support requests related to the Pet Simulator 99 Public API, please open an issue on the [GitHub repository](https://github.com/BIG-Games-LLC/ps99-public-api-docs/issues).

Explore the endpoints and integrate them into your applications! Happy coding!
