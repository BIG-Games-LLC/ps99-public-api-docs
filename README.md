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

Explore the endpoints and integrate them into your applications! Happy coding!
