from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import os

from team_assigner import TeamAssigner

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Store uploaded file path temporarily
uploaded_file_path = ""
uploaded_df = None  # To store DataFrame from Google Sheets


@app.route("/", methods=["GET", "POST"])
def index():
    global uploaded_file_path, uploaded_df
    if request.method == "POST":
        # Check if a file or URL is uploaded
        file = request.files.get("file")
        google_sheets_url = request.form.get("google_sheets_url")

        if not file and not google_sheets_url:
            return jsonify({"success": False}), 400

        # Read the CSV file into a pandas DataFrame
        if file and file.filename.endswith('.csv'):
            uploaded_file_path = "uploaded_file.csv"
            file.save(uploaded_file_path)
            uploaded_df = pd.read_csv(uploaded_file_path)
            return jsonify({"success": True})

        # Read the Google Sheets URL into a pandas DataFrame
        if google_sheets_url:
            sheet_id = google_sheets_url.split('/d/')[1].split('/')[0]
            csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv'
            uploaded_df = pd.read_csv(csv_url)

            if uploaded_df is not None:
                return jsonify({"success": True})
            else:
                return jsonify({"success": False}), 400

    return render_template("upload.html")


@app.route("/generate", methods=["POST"])
def generate():
    global uploaded_df
    if request.method == "POST":
        num_teams = int(request.form["num_teams"])
        max_team_size = int(request.form["max_team_size"])

        # Ensure the DataFrame is available
        if uploaded_df is None:
            return jsonify({"success": False, "message": "No data available."}), 400

        team_assigner = TeamAssigner(uploaded_df, num_teams, max_team_size)
        processed_data = team_assigner.assign_players_to_teams()

        # Create HTML to display the results
        html_content = f"""
            <table border="1">{processed_data.to_html(index=False)}</table>
            <a href="/download">Download CSV</a>
        """
        return jsonify({"html": html_content})


# Route to download the processed CSV
@app.route("/download")
def download_file():
    output_path = "output.csv"
    if os.path.exists(output_path):
        return send_file(output_path, as_attachment=True)
    else:
        return "No processed file available for download", 404


if __name__ == "__main__":
    app.run(debug=True)
