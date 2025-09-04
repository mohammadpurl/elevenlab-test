# Extract Info Service Updates

## Overview
This document describes the updates made to the `extract_info` service to align with the new booking flow and include all the new fields that were added to the chat system.

## Changes Made

### 1. Schema Updates (`api/schemas/extract_info_schema.py`)

#### Passenger Model Updates
- **Changed `fullName` to `name` and `lastName`**: Split full name into separate first and last name fields
- **Added `passportNumber`**: Passport number for each passenger  
- **Added `passengerType`**: Type of passenger (adult or infant)
- **Added `gender`**: Gender of the passenger

#### ExtractInfoResponse Updates
- **Added `travelType`**: Type of travel (arrival or departure)
- **Added `passengerCount`**: Total number of passengers
- **Added `flightNumber`**: Flight number for the booking
- **Added `additionalInfo`**: Optional additional information

### 2. Service Updates (`api/services/extract_info_service.py`)

#### Enhanced Prompt
The extraction prompt now includes:
- All new passenger fields (flight number, passport number, passenger type, gender)
- Travel type information
- Passenger count
- Additional information field
- Better instructions for extracting passenger information separately

#### Improved System Prompt
- More specific role definition as an expert information extraction assistant
- Better guidance for thorough and accurate extraction

## New Data Structure

### Before (Old Structure)
```json
{
  "airportName": "string",
  "travelDate": "string", 
  "flightNumber": "string",
  "passengers": [
    {
      "fullName": "string",
      "nationalId": "string",
      "luggageCount": "number"
    }
  ]
}
```

### After (New Structure)
```json
{
  "airportName": "string",
  "travelType": "string",  // "arrival" or "departure"
  "travelDate": "string",
  "passengerCount": "number",
  "flightNumber": "string",
  "passengers": [
    {
      "name": "string",
      "lastName": "string",
      "nationalId": "string",
      "passportNumber": "string",
      "luggageCount": "number",
      "passengerType": "string",  // "adult" or "infant"
      "gender": "string"
    }
  ],
  "additionalInfo": "string"  // optional
}
```

## Key Benefits

1. **Complete Information Extraction**: Now captures all the information collected during the booking conversation
2. **Per-Passenger Details**: Each passenger has their complete set of information
3. **Better Data Structure**: More organized and comprehensive data model with separate name fields
4. **Consistent with Chat System**: Aligns with the updated chat flow and data collection
5. **Improved Name Handling**: Separate first and last name fields for better data organization and processing

## Testing

Two test scripts are provided:

### 1. `test_extract_info.py`
- Tests with Persian conversation data
- Includes all new fields and passenger information
- Validates the complete data structure

### 2. `test_extract_info_en.py`  
- Tests with English conversation data
- Ensures the service works with both languages
- Same validation as Persian test

## Usage Example

```python
import requests

# Sample conversation data
conversation_data = {
    "messages": [
        {
            "id": "1",
            "text": "Hello, I want to book a flight ticket",
            "sender": "CLIENT"
        },
        # ... more messages
    ]
}

# Call the extract_info endpoint
response = requests.post(
    "http://localhost:8000/extractInfo/extract-info",
    json=conversation_data
)

# Extract the structured information
if response.status_code == 200:
    booking_info = response.json()
    print(f"Airport: {booking_info['airportName']}")
    print(f"Travel Type: {booking_info['travelType']}")
    print(f"Passengers: {booking_info['passengerCount']}")
    print(f"Flight Number: {booking_info['flightNumber']}")
    
    for i, passenger in enumerate(booking_info['passengers']):
        print(f"\nPassenger {i+1}:")
        print(f"  Name: {passenger['name']}")
        print(f"  Last Name: {passenger['lastName']}")
        print(f"  National ID: {passenger['nationalId']}")
        print(f"  Passport: {passenger['passportNumber']}")
        print(f"  Bags: {passenger['luggageCount']}")
        print(f"  Type: {passenger['passengerType']}")
        print(f"  Gender: {passenger['gender']}")
```

## Requirements

- OpenAI API key must be set in environment variables
- Server must be running on the specified port
- Valid conversation data with proper message structure

## Future Enhancements

1. **Language Detection**: Automatically detect conversation language
2. **Validation Rules**: Add business logic validation for extracted data
3. **Error Handling**: Better error messages for missing or invalid data
4. **Batch Processing**: Handle multiple conversations simultaneously
5. **Data Export**: Support for different export formats (CSV, Excel, etc.)
