import google.generativeai as genai
from crypto_utils import *
import os

# API Key provided by user
API_KEY = "AIzaSyCvHIk1SqFktRqZ7E4Da2fAqKbU3I-WRdg"

def analyze_patterns():
    genai.configure(api_key=API_KEY)

    # Use the 2.0 Flash model
    model = genai.GenerativeModel('gemini-2.0-flash')

    pulse_656 = get_pulse_656()
    k_160 = get_bit_fragment(pulse_656, 160)

    context = f"""
    Project Flamingo: Bitcoin Puzzle Resonance Analysis

    Sovereign Source (Pulse 656): {hex(pulse_656)}

    Foundational Alignment (Puzzle #130):
    - Target: 1CeUJyibjfGXhBoGc4Bm6iTkw8V9zKBZZi
    - Fragment: {hex(get_bit_fragment(pulse_656, 130))}
    - Relationship: d = (k // 8) * 8

    Apex Objective (Puzzle #160):
    - Target Address: 16vYfVp98SspFp9vTstEetf8x9J8fK13k
    - Pulse Fragment (k_160): {hex(k_160)}

    Project Parameters:
    - Multipliers: 128, 144
    - Q10 Scaling: (k * m) >> 10
    - Resonance Prime: 157
    - Mirror Multiplier: 3111 (from 3 * 1037)

    Analyze the pattern and suggest the most likely resonance scalar for the #160 Apex.
    Provide the answer as a single hex scalar and explain your reasoning based on "Grandmotherly Love."
    """

    print("--- INITIATING AI RESONANCE ANALYSIS ---")
    try:
        response = model.generate_content(context)
        print("\n[GEMINI INSIGHT]:")
        print(response.text)
    except Exception as e:
        print(f"\n[!] AI Link Failed: {e}")
        print("Please check your quota or wait for the cooling period.")

if __name__ == "__main__":
    analyze_patterns()
