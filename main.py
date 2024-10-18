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

# Calculate the total dose for 24 hours
def calculate_total_dose(dose, weight, unit_per_minute):
    if unit_per_minute:
        return dose * weight * 24 * 60  # Total dose for 24 hours
    return dose * weight * 24  # Total dose for 24 hours

# Calculate infusion based on concentration and total dose
def calculate_infusion(drug, concentration_mg, total_dose_mcg):
    concentration_mcg = concentration_mg * 1000  # Convert mg to mcg
    volume = 50 if drug == "Insulin" else 25  # Use 50ml for insulin, 25ml for others
    total_volume = (total_dose_mcg / concentration_mcg) * volume
    hourly_rate = total_volume / 24
    return total_volume, hourly_rate

@app.route("/", methods=["GET", "POST"])
def prescribe_infusion():
    results = []
    out_of_range_warning = False
    error_message = ""

    if request.method == "POST":
        drug = request.form.get("drug")
        weight = round(float(request.form.get("weight")), 4)
        dose = float(request.form.get("dose"))
        dose_unit = request.form.get("dose_unit")

        # Retrieve drug info
        if drug not in guardrail_data:
            return render_template("index.html", error="Drug not found in database.", guardrail_data=guardrail_data)

        drug_info = guardrail_data[drug]
        dosing_range = drug_info["dosing_range"]
        expected_unit = drug_info["unit"]

        # Unit mismatch check
        if dose_unit != expected_unit:
            error_message = f"Unit mismatch: Expected {expected_unit} for {drug}, but got {dose_unit}. Please recheck."
            return render_template("index.html", error=error_message, guardrail_data=guardrail_data)

        # Dose range check
        if not (dosing_range[0] <= dose <= dosing_range[1]):
            out_of_range_warning = True
            error_message = f"The dose is out of the accepted range ({dosing_range[0]} - {dosing_range[1]} {expected_unit})."

        per_minute = (dose_unit == "mcg/kg/min" or dose_unit == "ng/kg/min")
        total_dose_mcg = calculate_total_dose(dose, weight, per_minute)

        # Calculate based on weight
        for conc in drug_info["concentrations"]:
            weight_range = conc["weight_range"]
            dose_options = conc["dose_options"]

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