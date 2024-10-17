from flask import Flask, request, render_template

# Initialize Flask app
app = Flask(__name__)

# Guardrail data with updated units and corrected concentrations
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
    },
    # Other drugs can be added similarly...
}

def calculate_total_dose(dose, weight, per_minute=False):
    if per_minute:
        dose *= 60  # Convert mcg/kg/min to mcg/kg/hour if necessary
    return dose * weight * 24  # Total dose for 24 hours

def calculate_infusion(volume, concentration, total_dose):
    total_volume = total_dose / (concentration * volume)
    hourly_rate = total_volume / 24
    return total_volume, hourly_rate

@app.route("/", methods=["GET", "POST"])
def prescribe_infusion():
    results = []
    out_of_range_warning = False
    unit_mismatch = False
    error_message = ""
    
    if request.method == "POST":
        drug = request.form.get("drug")
        weight = float(request.form.get("weight"))
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

        # Calculate total dose and infusion details
        total_dose = calculate_total_dose(dose, weight, per_minute=(dose_unit == "mcg/kg/min"))

        # Determine appropriate concentration based on weight
        for conc in drug_info["concentrations"]:
            weight_range = conc["weight_range"]
            dose_options = conc["dose_options"]
            
            if (weight < 1 and weight_range == "<1kg") or \
               (1 <= weight <= 2.4 and weight_range == "1-2.4kg") or \
               (weight > 2.5 and weight_range == ">2.5kg"):
                for dose_option in dose_options:
                    total_volume, hourly_rate = calculate_infusion(25, dose_option, total_dose)
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

if __name__ == "__main__":
    app.run(debug=True)
