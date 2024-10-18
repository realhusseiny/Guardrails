from flask import Flask, request, render_template
import os

# Initialize Flask app
app = Flask(__name__)

# Guardrail data with all drugs, updated units, and corrected concentrations
guardrail_data = {
    "Adrenaline": {
        "dosing_range": (0.05, 1.5),
        "unit": "mcg/kg/min",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.25, 1.25]},
            {"weight_range": "1-2.4kg", "dose_options": [0.75, 3]},
            {"weight_range": ">2.5kg", "dose_options": [1.25, 5]},
        ],
    },
    "Dobutamine": {
        "dosing_range": (5, 40),
        "unit": "mcg/kg/min",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [25, 100]},
            {"weight_range": "1-2.4kg", "dose_options": [75, 150]},
            {"weight_range": ">2.5kg", "dose_options": [100, 150]},
        ],
    },
    "Dopamine": {
        "dosing_range": (7.5, 20),
        "unit": "mcg/kg/min",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [10, 50]},
            {"weight_range": "1-2.4kg", "dose_options": [25, 100]},
            {"weight_range": ">2.5kg", "dose_options": [75, 200]},
        ],
    },
    "Midazolam low": {
        "dosing_range": (30, 120),
        "unit": "mcg/kg/hr",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.75, 3]},
            {"weight_range": "1-2.4kg", "dose_options": [1, 4]},
            {"weight_range": ">2.5kg", "dose_options": [1.5, 4.5]},
        ],
    },
    "Midazolam high": {
        "dosing_range": (120, 300),
        "unit": "mcg/kg/hr",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [2, 5]},
            {"weight_range": "1-2.4kg", "dose_options": [4, 12]},
            {"weight_range": ">2.5kg", "dose_options": [8, 20]},
        ],
    },
    "Morphine": {
        "dosing_range": (10, 40),
        "unit": "mcg/kg/hr",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.5, 1.5]},
            {"weight_range": "1-2.4kg", "dose_options": [1, 5]},
            {"weight_range": ">2.5kg", "dose_options": [2.5, 7.5]},
        ],
    },
    "Noradrenaline": {
        "dosing_range": (0.1, 1.5),
        "unit": "mcg/kg/min",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.3, 3]},
            {"weight_range": "1-2.4kg", "dose_options": [0.6, 3]},
            {"weight_range": ">2.5kg", "dose_options": [1.2, 6]},
        ],
    },
    "Prostaglandin": {
        "dosing_range": (5, 100),
        "unit": "ng/kg/min",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [25, 200]},
            {"weight_range": "1-2.4kg", "dose_options": [50, 0.3]},
            {"weight_range": ">2.5kg", "dose_options": [75, 0.5]},
        ],
    },
    "Tolazoline (PPHN)": {
        "dosing_range": (0.25, 2),
        "unit": "mg/kg/hr",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [50, 100]},
            {"weight_range": "1-2.4kg", "dose_options": [100, 200]},
            {"weight_range": ">2.5kg", "dose_options": [150, 300]},
        ],
    },
    "Vecuronium": {
        "dosing_range": (1, 1),
        "unit": "mcg/kg/min",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [1.5]},
            {"weight_range": "1-2.4kg", "dose_options": [4]},
            {"weight_range": ">2.5kg", "dose_options": [7.5]},
        ],
    },
    "Insulin": {
        "dosing_range": (0.05, 0.5),  # Updated to 0.05u/kg/hr
        "unit": "u/kg/hr",  # Added unit for insulin
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [5, 15]},
            {"weight_range": "1-2.4kg", "dose_options": [10, 25]},
            {"weight_range": ">2.5kg", "dose_options": [20, 50]},
        ],
    },
    "Rocuronium": {
        "dosing_range": (300, 600),
        "unit": "mcg/kg/hr",
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [20]},
            {"weight_range": "1-2.4kg", "dose_options": [35]},
            {"weight_range": ">2.5kg", "dose_options": [75]},
        ],
    }
}

@app.route("/", methods=["GET", "POST"])
def prescribe_infusion():
    results = []
    out_of_range_warning = False
    unit_mismatch = False
    error_message = ""
    
    if request.method == "POST":
        drug = request.form.get("drug")
        weight = round(float(request.form.get("weight")), 4)  # Accepts weight up to 4 decimal places
        dose = float(request.form.get("dose"))
        dose_unit = request.form.get("dose_unit")

        # Retrieve drug info
        if drug not in guardrail_data:
            return render_template("index.html", error="Drug not found in database.", guardrail_data=guardrail_data)
        
        drug_info = guardrail_data[drug]
        dosing_range = drug_info["dosing_range"]
        expected_unit = drug_info["unit"]

        # Check if the dose unit matches the expected unit for the drug
        if dose_unit != expected_unit:
            unit_mismatch = True
            error_message = f"Unit mismatch: Expected {expected_unit} for {drug}, but got {dose_unit}. Please recheck."
            return render_template("index.html", error=error_message, guardrail_data=guardrail_data)
        
        # Check if the dose is within the accepted range
        if not (dosing_range[0] <= dose <= dosing_range[1]):
            out_of_range_warning = True
            error_message = f"The dose is out of the accepted range ({dosing_range[0]} - {dosing_range[1]} {expected_unit})."

        # Calculate total dose (mcg/day), considering whether it's per minute or per hour
        per_minute = (dose_unit == "mcg/kg/min" or dose_unit == "ng/kg/min")
        total_dose_mcg = calculate_total_dose(dose, weight, per_minute)

        # Determine appropriate concentration based on weight
        for conc in drug_info["concentrations"]:
            weight_range = conc["weight_range"]
            dose_options = conc["dose_options"]
            
            # Adjusted the weight condition to include 2.5 kg in the ">2.5kg" range
            if (weight < 1 and weight_range == "<1kg") or \
               (1 <= weight <= 2.4 and weight_range == "1-2.4kg") or \
               (weight >= 2.5 and weight_range == ">2.5kg"):
                for dose_option in dose_options:
                    total_volume, hourly_rate = calculate_infusion(drug, dose_option, total_dose_mcg)
                    results.append({
                        "concentration": dose_option,
                        "total_volume": round(total_volume, 2),
                        "hourly_rate": round(hourly_rate, 2)
                    })
        
        return render_template("result.html", drug=drug, weight=weight, dose=dose, unit=expected_unit,
                               results=results, dose_range=dosing_range,
                               out_of_range_warning=out_of_range_warning,
                               error_message=error_message, guardrail_data=guardrail_data)

    return render_template("index.html", guardrail_data=guardrail_data)

# Function to calculate total dose
def calculate_total_dose(dose, weight, unit_per_minute):
    # If the unit is per minute, multiply by 60 to get the dose per hour
    if unit_per_minute:
        return dose * weight * 24 * 60  # Total dose for 24 hours
    else:
        return dose * weight * 24  # Total dose for 24 hours without multiplying by 60

# Function to calculate infusion details
def calculate_infusion(drug, concentration_mg, total_dose_mcg):
    concentration_mcg = concentration_mg * 1000  # Convert mg to mcg
    
    # Use the correct volume (50 ml for Insulin, 25 ml for others)
    if drug == "Insulin":
        volume = 50
    else:
        volume = 25
    
    total_volume = (total_dose_mcg / concentration_mcg) * volume  # Calculate the total volume in ml
    hourly_rate = total_volume / 24  # Calculate the hourly rate (ml/hr)
    
    return total_volume, hourly_rate

# Ensure the app listens on the correct port for the platform
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))  # Use the port provided by the environment or default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)