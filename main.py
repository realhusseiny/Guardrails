from flask import Flask, request, render_template

# Initialize Flask app
app = Flask(__name__)

# Guardrail data with all drugs and concentrations
guardrail_data = {
    "Adrenaline": {
        "dosing_range": (0.05, 1.5),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.25, 1.25]},
            {"weight_range": "1-2.4kg", "dose_options": [0.75, 3]},
            {"weight_range": ">2.5kg", "dose_options": [1.25, 5]},
        ],
    },
    "Dopamine": {
        "dosing_range": (7.5, 20),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [10, 50]},
            {"weight_range": "1-2.4kg", "dose_options": [25, 100]},
            {"weight_range": ">2.5kg", "dose_options": [75, 200]},
        ],
    },
    "Midazolam low": {
        "dosing_range": (30, 120),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.75, 3]},
            {"weight_range": "1-2.4kg", "dose_options": [1.5, 4.5]},
            {"weight_range": ">2.5kg", "dose_options": [3, 7.5]},
        ],
    },
    "Midazolam high": {
        "dosing_range": (120, 300),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [2, 5]},
            {"weight_range": "1-2.4kg", "dose_options": [4, 12]},
            {"weight_range": ">2.5kg", "dose_options": [6, 15]},
        ],
    },
    "Morphine": {
        "dosing_range": (10, 40),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.5, 1.5]},
            {"weight_range": "1-2.4kg", "dose_options": [1, 5]},
            {"weight_range": ">2.5kg", "dose_options": [2, 7.5]},
        ],
    },
    "Noradrenaline": {
        "dosing_range": (0.1, 1.5),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [0.3, 1.5]},
            {"weight_range": "1-2.4kg", "dose_options": [0.6, 3]},
            {"weight_range": ">2.5kg", "dose_options": [1.2, 6]},
        ],
    },
    "Prostaglandin": {
        "dosing_range": (5, 100),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [25, 100]},
            {"weight_range": "1-2.4kg", "dose_options": [50, 200]},
            {"weight_range": ">2.5kg", "dose_options": [100, 500]},
        ],
    },
    "Tolazoline (for arterial spasm)": {
        "dosing_range": None,
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [5]},
            {"weight_range": "1-2.4kg", "dose_options": [5]},
            {"weight_range": ">2.5kg", "dose_options": [5]},
        ],
    },
    "Tolazoline (PPHN)": {
        "dosing_range": (0.25, 2),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [50, 100]},
            {"weight_range": "1-2.4kg", "dose_options": [100, 200]},
            {"weight_range": ">2.5kg", "dose_options": [150, 300]},
        ],
    },
    "Vecuronium": {
        "dosing_range": (1, 1),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [1]},
            {"weight_range": "1-2.4kg", "dose_options": [2]},
            {"weight_range": ">2.5kg", "dose_options": [4]},
        ],
    },
    "Insulin": {
        "dosing_range": None,
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [5, 15]},
            {"weight_range": "1-2.4kg", "dose_options": [10, 25]},
            {"weight_range": ">2.5kg", "dose_options": [20, 50]},
        ],
    },
    "Rocuronium": {
        "dosing_range": (300, 600),
        "concentrations": [
            {"weight_range": "<1kg", "dose_options": [20]},
            {"weight_range": "1-2.4kg", "dose_options": [35]},
            {"weight_range": ">2.5kg", "dose_options": [75]},
        ],
    },
}

def calculate_total_dose(dose, weight, per_minute=False):
    if per_minute:
        dose *= 60  # Convert per minute dose to per hour
    return dose * weight * 24  # Total dose for 24 hours

def calculate_infusion(volume, concentration, total_dose):
    total_volume = total_dose / (concentration * volume)
    hourly_rate = total_volume / 24
    return total_volume, hourly_rate

@app.route("/", methods=["GET", "POST"])
def prescribe_infusion():
    results = []
    if request.method == "POST":
        drug = request.form.get("drug")
        weight = float(request.form.get("weight"))
        dose = float(request.form.get("dose"))

        if drug not in guardrail_data:
            return render_template("index.html", error="Drug not found in database.")

        # Retrieve drug info
        drug_info = guardrail_data[drug]
        dosing_range = drug_info["dosing_range"]

        # Check if dose is within range if there's a range
        if dosing_range and not dosing_range[0] <= dose <= dosing_range[1]:
            return render_template("index.html", error="Dose out of range.")

        # Calculate total dose
        total_dose = calculate_total_dose(dose, weight, per_minute=True)

        # Identify the concentration based on weight
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

        return render_template("result.html", drug=drug, weight=weight, dose=dose, results=results)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
