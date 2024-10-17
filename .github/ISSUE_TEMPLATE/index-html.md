---
name: index.html
about: Describe this issue template's purpose here.
title: ''
labels: ''
assignees: ''

---

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Infusion Prescriber</title>
</head>
<body>
    <h1>Infusion Prescriber</h1>
    <form method="post">
        <label for="drug">Drug Name:</label>
        <input type="text" id="drug" name="drug" required><br><br>

        <label for="weight">Weight (kg):</label>
        <input type="number" id="weight" name="weight" step="0.1" required><br><br>

        <label for="dose">Dose (mcg/kg/min):</label>
        <input type="number" id="dose" name="dose" step="0.1" required><br><br>

        <button type="submit">Calculate</button>
    </form>
    {% if error %}
    <p style="color:red;">{{ error }}</p>
    {% endif %}
</body>
</html>
