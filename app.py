from flask import Flask, request, send_from_directory, jsonify, render_template
import pandas as pd
import os
import logging
import uuid
from werkzeug.utils import secure_filename
from lexer import Lexer
from parser import Parser
from code_generator import CodeGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("backend/app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, static_folder="../frontend", static_url_path="/")

# Folder to store uploaded and processed files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_balanced_parentheses(s):
    stack = []
    for c in s:
        if c == '(':
            stack.append(c)
        elif c == ')':
            if not stack:
                return False
            stack.pop()
    return not stack

# Serve Frontend
@app.route('/')
def serve_index():
    return app.send_static_file("index.html")

# DSL Processing
@app.route('/run-script', methods=['POST'])
def run_script():
    file = request.files.get('file')
    script = request.form.get('script', '').strip()
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "No valid file uploaded"}), 400

    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_id = str(uuid.uuid4())
    upload_filename = f"input_{unique_id}{file_ext}"
    upload_path = os.path.join(UPLOAD_FOLDER, upload_filename)
    file.save(upload_path)

    # Load the DataFrame
    try:
        if file_ext == '.csv':
            df = pd.read_csv(upload_path)
        elif file_ext == '.json':
            df = pd.read_json(upload_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(upload_path)
        else:
            return jsonify({"error": "Unsupported file format"}), 400
    except Exception as e:
        logging.error(f"File read error: {e}")
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    logging.info(f"Received DSL Script:\n{script}")

    try:
        # Compiler pipeline: Lexer -> Parser -> CodeGen -> Exec
        lexer = Lexer(script)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        commands = parser.parse()
        # Check for malformed commands before codegen
        for cmd in commands:
            if not is_balanced_parentheses(cmd):
                logging.error(f"Malformed command (unbalanced parentheses): {cmd}")
                return jsonify({"error": f"Malformed command: {cmd}"}), 400
        codegen = CodeGenerator(commands)
        code = codegen.generate_code()
        logging.info(f"Generated code:\n{code}")

        # Determine output filename from SAVE command in commands
        output_fname = None
        import ast
        for cmd in commands:
            if cmd.strip().startswith("df.to_csv(") or cmd.strip().startswith("df.to_json("):
                try:
                    # Parse the command as Python code to extract the first argument
                    tree = ast.parse(cmd.strip())
                    call = tree.body[0].value
                    if call.args and isinstance(call.args[0], ast.Str):
                        output_fname = call.args[0].s
                        break
                except Exception:
                    continue
        if not output_fname:
            output_fname = f"processed_{unique_id}.csv"

        processed_filename = f"processed_{unique_id}.csv" if output_fname.endswith('.csv') else f"processed_{unique_id}.json"
        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)

        # Prepare the execution environment
        exec_globals = {'pd': pd, 'df': df}
        exec_locals = {}
        try:
            exec(code, exec_globals, exec_locals)
            # Prefer df from exec_locals if present (code may assign to local scope)
            if 'df' in exec_locals:
                df_result = exec_locals['df']
            else:
                df_result = exec_globals.get('df', df)
        except Exception as e:
            logging.error(f"Execution error: {e}\nCode was:\n{code}")
            return jsonify({"error": f"Execution failed: {str(e)}"}), 400

        # Save the processed file
        try:
            if df_result is None or (hasattr(df_result, 'empty') and df_result.empty):
                logging.error("Processed DataFrame is empty or None.")
                return jsonify({"error": "Processed data is empty. Nothing to save."}), 400
            if processed_filename.endswith('.csv'):
                df_result.to_csv(processed_path, index=False)
            elif processed_filename.endswith('.json'):
                df_result.to_json(processed_path, orient='records', lines=True)
            else:
                return jsonify({"error": "Unsupported output format"}), 400
            # Double-check file was created
            if not os.path.exists(processed_path):
                logging.error(f"Processed file not found after save: {processed_path}")
                return jsonify({"error": "Processed file could not be created."}), 500
        except Exception as e:
            logging.error(f"File save error: {e}")
            return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

        logging.info(f"Saved processed file: {processed_path}")
        preview = None
        try:
            # Replace NaN/NaT/inf with None for valid JSON
            preview_df = df_result.head(10)
            preview = preview_df.where(pd.notnull(preview_df), None).to_dict(orient='records')
        except Exception:
            preview = None
        return jsonify({"message": "Processing complete", "filename": processed_filename, "preview": preview})
    except Exception as e:
        logging.error(f"Processing error: {e}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    finally:
        try:
            os.remove(upload_path)
        except Exception:
            pass

# Download processed file
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    if filename == "app.log":
        # Allow download of backend log
        log_path = os.path.join("backend", "app.log")
        if not os.path.exists(log_path):
            return jsonify({"error": "Log file not found"}), 404
        return send_from_directory("backend", "app.log", as_attachment=True)
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(file_path):
        logging.error(f"Download requested but file not found: {file_path}")
        return jsonify({"error": "File not found"}), 404
    try:
        return send_from_directory(PROCESSED_FOLDER, filename, as_attachment=True)
    except Exception as e:
        logging.error(f"Error sending file {filename}: {e}")
        return jsonify({"error": f"Failed to send file: {str(e)}"}), 500

@app.route('/Documentation.txt')
def serve_documentation():
    # Try backend first, then frontend
    backend_doc = os.path.join(os.path.dirname(__file__), 'Documentation.txt')
    frontend_doc = os.path.abspath(os.path.join(app.static_folder, 'Documentation.txt'))
    if os.path.exists(backend_doc):
        return send_from_directory(os.path.dirname(backend_doc), 'Documentation.txt')
    elif os.path.exists(frontend_doc):
        return send_from_directory(os.path.dirname(frontend_doc), 'Documentation.txt')
    else:
        return "Documentation not found", 404

if __name__ == '__main__':
    # For production, use a WSGI server (e.g., gunicorn)
    app.run(debug=True)
