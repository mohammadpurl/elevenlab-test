# Multiple Passenger Implementation

## Problem Description

The original system had a critical issue: when a user declared more than 1 passenger, the assistant would only ask for information for one person and wouldn't proceed to ask for the next passenger's information. The flight number, flight date, and departure airport were the same for all passengers, but personal information for each passenger needed to be collected separately.

**Additionally**, the system had another major flaw: it would mechanically move from one question to the next without validating user responses, making it feel like talking to a machine rather than an intelligent assistant.

## Solution Overview

We've implemented a comprehensive solution that:

1. **Tracks Multiple Passengers**: The system now properly tracks which passenger we're currently collecting information for
2. **Sequential Data Collection**: Information is collected for each passenger completely before moving to the next
3. **Shared Flight Information**: Flight number, date, and airport information is collected once and shared across all passengers
4. **Individual Passenger Data**: Each passenger's personal information is stored separately
5. **QR Code Generation**: After collecting all information, a QR code is shown for final confirmation
6. **Intelligent Response Validation**: The system now validates user responses and provides appropriate feedback instead of just moving mechanically to the next question

## Technical Implementation

### 1. Enhanced BookingState Class

The `BookingState` class has been significantly enhanced:

```python
class BookingState:
    def __init__(self):
        self.current_step = 0
        self.retry_count = 0
        self.current_passenger_index = 0  # Track which passenger we're collecting info for
        self.passenger_count = 0  # Total number of passengers
        self.collected_data: Dict[str, str] = {
            "origin_airport": "",
            "travel_type": "",
            "travel_date": "",
            "passenger_count": "",
            "additional_info": "",
        }
        # Store individual passenger data
        self.passengers_data: List[Dict[str, str]] = []
```

### 2. Passenger Data Structure

Each passenger's information is stored in a structured format:

```python
class PassengerData(BaseModel):
    name: str = ""
    nationalId: str = ""    
    passportNumber: str = ""
    baggageCount: str = ""
    passengerType: str = ""  # "adult" or "infant"
    gender: str = ""
```

### 3. Smart Question Flow

The system automatically determines the next question based on:
- Current step in the conversation
- Which passenger we're collecting information for
- Whether all information for the current passenger has been collected

### 4. New API Endpoints

#### Get Booking State
```
GET /booking-state/{session_id}
```

Returns the current booking state including all collected passenger information.

### 5. Intelligent Response Validation System

**The most important improvement**: The system now validates user responses before proceeding to the next question.

#### Validation Features:
- **Empty Response Detection**: Catches empty or whitespace-only responses
- **Format Validation**: Validates data formats (e.g., national ID must be 10 digits)
- **Range Validation**: Ensures values are within reasonable ranges
- **Type Validation**: Confirms responses match expected types
- **Helpful Error Messages**: Provides clear feedback on what went wrong

#### Example Validation Rules:
```python
# National ID validation
if question_type == "national_id":
    cleaned_id = "".join(filter(str.isdigit, user_message))
    if len(cleaned_id) != 10:
        return {
            "is_valid": False,
            "error_message": "کد ملی باید دقیقاً ۱۰ رقم باشد."
        }

# Passenger count validation
elif question_type == "passenger_count":
    try:
        count = int(user_message)
        if count < 1 or count > 20:
            return {
                "is_valid": False,
                "error_message": "تعداد مسافران باید بین ۱ تا ۲۰ نفر باشد."
            }
    except ValueError:
        return {
            "is_valid": False,
            "error_message": "لطفاً تعداد مسافران را به صورت عدد وارد کنید."
        }
```

## Conversation Flow

### Step-by-Step Process

1. **Airport Information** (Shared)
   - Origin airport name
   - Travel type (arrival/departure)
   - Travel date

2. **Passenger Count**
   - Total number of passengers

3. **For Each Passenger** (Sequential)
   - Full name
   - National ID
   - Flight number (shared, but collected per passenger)
   - Passport number
   - Baggage count
   - Passenger type (adult/infant)
   - Gender

4. **Additional Information**
   - Any extra details

5. **Completion**
   - Confirmation message
   - QR code for final review

### Example Flow for 2 Passengers

```
User: "فرودگاه امام خمینی"
Assistant: "نام فرودگاه مبدا رو بفرمایید."

User: "خروجی"
Assistant: "پروازتون ورودی به فرودگاهه یا خروجی؟"

User: "۱۵ آگوست ۲۰۲۴"
Assistant: "تاریخ سفر رو به میلادی بفرمایید."

User: "۲ نفر"
Assistant: "تعداد دقیق مسافران چند نفر است؟"

User: "احمد محمدی"
Assistant: "نام و نام خانوادگی مسافر ۱ رو بفرمایید."

User: "۱۲۳۴۵۶۷۸۹۰"
Assistant: "کد ملی مسافر ۱ رو بفرمایید."

User: "IR123"
Assistant: "شماره پرواز مسافر ۱ رو بفرمایید."

User: "A12345678"
Assistant: "شماره گذرنامه مسافر ۱ رو بفرمایید."

User: "۲"
Assistant: "تعداد چمدان‌های مسافر ۱ رو بفرمایید."

User: "بزرگسال"
Assistant: "نوع مسافر ۱ بزرگسال است یا نوزاد؟"

User: "مرد"
Assistant: "جنسیت مسافر ۱ چیه؟"

User: "علی احمدی"
Assistant: "نام و نام خانوادگی مسافر ۲ رو بفرمایید."

User: "۰۹۸۷۶۵۴۳۲۱"
Assistant: "کد ملی مسافر ۲ رو بفرمایید."

User: "IR123"
Assistant: "شماره پرواز مسافر ۲ رو بفرمایید."

User: "B87654321"
Assistant: "شماره گذرنامه مسافر ۲ رو بفرمایید."

User: "۱"
Assistant: "تعداد چمدان‌های مسافر ۲ رو بفرمایید."

User: "بزرگسال"
Assistant: "نوع مسافر ۲ بزرگسال است یا نوزاد؟"

User: "مرد"
Assistant: "جنسیت مسافر ۲ چیه؟"

User: "هیچ توضیح اضافه‌ای ندارم"
Assistant: "توضیح اضافه‌ای که می‌خواید بگید؟"

Assistant: "عالی! همه اطلاعات شما دریافت شد. حالا می‌توانید از طریق کیو آر کد اطلاعات را مشاهده و در صورت نیاز اصلاح کنید."

Assistant: "از طریق کیو آر کد می‌توانی اطلاعات را در فرم ببینی و آن را اصلاح کنی."

Assistant: "راستی اگه الان فرودگاه امام خمینی هستی می‌تونم هماهنگ کنم بچه‌های ترنسفر درب خروجی سوارت کنند و ترنسفرت رو مهمون من باشی، نظرت چیه دوست من؟"
```

### Validation Examples

**Before (Old System):**
```
User: "" (empty response)
Assistant: [Moves to next question without validation] ❌

User: "ا" (too short airport name)
Assistant: [Moves to next question without validation] ❌

User: "نامعتبر" (invalid travel type)
Assistant: [Moves to next question without validation] ❌
```

**After (New System):**
```
User: "" (empty response)
Assistant: "لطفاً پاسخ خود را وارد کنید." ✅

User: "ا" (too short airport name)
Assistant: "نام فرودگاه باید حداقل ۳ کاراکتر باشد." ✅

User: "نامعتبر" (invalid travel type)
Assistant: "نوع سفر باید 'ورودی' یا 'خروجی' باشد." ✅
```

## Key Features

### 1. **Automatic Passenger Progression**
- After collecting all information for one passenger, the system automatically moves to the next
- No manual intervention required

### 2. **Context-Aware Questions**
- Questions are personalized for each passenger (e.g., "نام و نام خانوادگی مسافر ۲ رو بفرمایید")
- Clear indication of which passenger's information is being collected

### 3. **Data Validation**
- Each passenger's information is collected completely before proceeding
- Shared information (flight number, date, airport) is maintained across all passengers

### 4. **Session Management**
- Each conversation session maintains its own state
- Multiple concurrent users can be handled independently

### 5. **QR Code Generation**
- After collecting all information, a QR code is generated
- Users can review and modify information through the QR code

### 6. **Intelligent Response Validation** ⭐ **NEW**
- **No more mechanical progression**: System validates responses before moving forward
- **Helpful error messages**: Clear feedback on what needs to be corrected
- **Data quality assurance**: Ensures collected information meets requirements
- **User experience improvement**: Feels like talking to an intelligent assistant, not a machine

## Testing

### Test Scripts
- **`test_multiple_passengers.py`** - Tests multiple passenger functionality
- **`test_validation_system.py`** - Tests the new validation system

To run the validation test:
```bash
python test_validation_system.py
```

### Manual Testing
1. Start a conversation with the assistant
2. Try entering invalid responses (empty, too short, wrong format)
3. Verify that the system shows validation errors and repeats questions
4. Enter valid responses and confirm progression
5. Declare multiple passengers and verify proper handling
6. Confirm QR code generation at completion

## API Usage

### Frontend Integration

The frontend can use the new `/booking-state/{session_id}` endpoint to:
- Display current progress
- Show collected information for each passenger
- Provide a summary before final confirmation

### Example Response
```json
{
  "origin_airport": "فرودگاه امام خمینی",
  "travel_type": "خروجی",
  "travel_date": "۱۵ آگوست ۲۰۲۴",
  "passenger_count": "۲",
  "passengers_data": [
    {
      "name": "احمد محمدی",
      "nationalId": "۱۲۳۴۵۶۷۸۹۰",
      "flightNumber": "IR123",
      "passportNumber": "A12345678",
      "baggageCount": "۲",
      "passengerType": "بزرگسال",
      "gender": "مرد"
    },
    {
      "name": "علی احمدی",
      "nationalId": "۰۹۸۷۶۵۴۳۲۱",
      "flightNumber": "IR123",
      "passportNumber": "B87654321",
      "baggageCount": "۱",
      "passengerType": "بزرگسال",
      "gender": "مرد"
    }
  ],
  "additional_info": "هیچ توضیح اضافه‌ای ندارم"
}
```

## Benefits

1. **Complete Passenger Coverage**: All passengers are now properly handled
2. **Better User Experience**: Clear progression through passenger information collection
3. **Data Integrity**: Complete information collection before proceeding
4. **Scalability**: Supports any number of passengers
5. **Maintainability**: Clean, structured code that's easy to extend
6. **Intelligent Interaction**: **No more mechanical responses - system now understands and validates user input** ⭐

## Future Enhancements

1. **Advanced Validation Rules**: Add more sophisticated validation (e.g., passport number format, date validation)
2. **Data Export**: Export collected data in various formats (PDF, CSV)
3. **Integration**: Connect with airline booking systems
4. **Analytics**: Track conversation patterns and user behavior
5. **Multi-language Support**: Extend to more languages beyond Persian and English
6. **Machine Learning**: Learn from user patterns to improve validation rules

## Conclusion

This implementation successfully solves **both** original problems:

1. **Multiple Passenger Issue**: ✅ Fixed - System now properly handles multiple passengers
2. **Mechanical Question Progression**: ✅ Fixed - System now validates responses and provides intelligent feedback

The system now:
- Properly tracks multiple passengers
- Collects complete information for each passenger
- Maintains shared flight information
- Provides a clear, step-by-step conversation flow
- Generates QR codes for final confirmation
- **Most importantly**: Validates user responses and provides helpful feedback instead of just moving mechanically to the next question

**The result**: Users now feel like they're talking to an intelligent, understanding assistant rather than a mechanical question machine. The system provides a much better user experience for group bookings with proper validation and feedback at every step.
