from langchain_google_genai import ChatGoogleGenerativeAI
import json
import re


def extract_shipment_data(text: str, api_key: str) -> dict:
    if not text or not text.strip():
        return {"error": "No document text available. Please upload a document first."}

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",   # gemini-2.5-flash is not a valid public model string
        temperature=0,
        google_api_key=api_key,
    )

    prompt = f"""Extract the following fields from the logistics document.

Return ONLY valid JSON. No markdown. No explanation. No code fences.

Fields to extract:
- shipment_id
- shipper
- consignee
- pickup_datetime
- delivery_datetime
- equipment_type
- mode
- rate
- currency
- weight
- carrier_name

If a field is missing or unclear, set its value to null.

Document:
{text}"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Strip markdown fences if model still adds them
        content = re.sub(r"```json", "", content)
        content = re.sub(r"```", "", content).strip()

        json_start = content.find("{")
        json_end = content.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            return {"error": "No JSON object found in response", "raw": content}

        clean_json = content[json_start:json_end]
        return json.loads(clean_json)

    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing failed: {str(e)}", "raw": content}
    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}