from flask import Flask, render_template, request, redirect, send_file, url_for
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file.filename == '':
        return 'No file selected'

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Determine file type and read accordingly
    if file.filename.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif file.filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(filepath)
    elif file.filename.endswith('.json'):
        df = pd.read_json(filepath)
    else:
        return 'Unsupported file format'

    df_html = df.head(20).to_html(classes='table table-bordered', index=False)

    # Missing values and stats
    missing_values = df.isnull().sum().to_dict()
    data_types = df.dtypes.astype(str).to_dict()
    summary_stats = df.describe(include='all').transpose().fillna('').to_dict('index')

    return render_template('preview.html', 
                           table=df_html,
                           filename=file.filename,
                           missing=missing_values,
                           dtypes=data_types,
                           stats=summary_stats)

@app.route('/clean', methods=['POST'])
def clean():
    filename = request.form['filename']
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Determine file type and read accordingly
    if filename.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif filename.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(filepath)
    elif filename.endswith('.json'):
        df = pd.read_json(filepath)
    else:
        return 'Unsupported file format'

    if 'drop_na' in request.form:
        df = df.dropna()
    elif 'fill_na' in request.form:
        df = df.fillna(method='ffill').fillna(method='bfill')

    if 'normalize' in request.form:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())

    if 'encode' in request.form:
        categorical_cols = df.select_dtypes(include=['object']).columns
        df = pd.get_dummies(df, columns=categorical_cols)

    cleaned_filename = 'cleaned_' + filename
    cleaned_filepath = os.path.join(UPLOAD_FOLDER, cleaned_filename)

    # Save file in its original format
    if filename.endswith('.csv'):
        df.to_csv(cleaned_filepath, index=False)
    elif filename.endswith(('.xls', '.xlsx')):
        df.to_excel(cleaned_filepath, index=False)
    elif filename.endswith('.json'):
        df.to_json(cleaned_filepath, orient='records', lines=True)

    return send_file(cleaned_filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True,port=8000)