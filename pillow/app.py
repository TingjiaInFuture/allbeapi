from flask import Flask, request, jsonify, send_file
from PIL import Image, ImageFilter, UnidentifiedImageError
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

@app.route('/pillow/process-image', methods=['POST'])
def process_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    operations = request.form.getlist('operations') # e.g., ["resize:200,200", "grayscale"]
    output_format = request.form.get('output_format', 'PNG').upper()

    if not operations:
        return jsonify({'error': 'No operations specified'}), 400

    try:
        img = Image.open(file.stream)
    except UnidentifiedImageError:
        return jsonify({'error': 'Cannot identify image file'}), 400
    except Exception as e:
        return jsonify({'error': f'Error opening image: {str(e)}'}), 500

    original_format = img.format

    for operation_str in operations:
        parts = operation_str.split(':')
        op_name = parts[0].lower()
        op_args = parts[1] if len(parts) > 1 else None

        try:
            if op_name == 'resize':
                if not op_args:
                    return jsonify({'error': 'Resize operation requires dimensions (width,height)'}), 400
                dims = tuple(map(int, op_args.split(',')))
                if len(dims) != 2:
                     return jsonify({'error': 'Resize operation requires 2 dimensions (width,height)'}), 400
                img = img.resize(dims)
            elif op_name == 'rotate':
                if not op_args:
                    return jsonify({'error': 'Rotate operation requires angle'}), 400
                img = img.rotate(int(op_args))
            elif op_name == 'grayscale':
                img = img.convert('L')
            elif op_name == 'blur':
                radius = float(op_args) if op_args else 2
                img = img.filter(ImageFilter.GaussianBlur(radius))
            elif op_name == 'crop': # format: x,y,width,height
                if not op_args:
                    return jsonify({'error': 'Crop operation requires box coordinates (x,y,width,height)'}), 400
                box = tuple(map(int, op_args.split(',')))
                if len(box) != 4:
                    return jsonify({'error': 'Crop operation requires 4 coordinates (x,y,width,height)'}), 400
                # Pillow crop is (left, upper, right, lower)
                img = img.crop((box[0], box[1], box[0] + box[2], box[1] + box[3]))
            # Add more operations as needed
            else:
                return jsonify({'error': f'Unknown operation: {op_name}'}), 400
        except ValueError as ve:
            return jsonify({'error': f'Invalid argument for {op_name}: {str(ve)}'}), 400
        except Exception as e:
            return jsonify({'error': f'Error during operation {op_name}: {str(e)}'}), 500

    img_io = io.BytesIO()
    try:
        # Use original format if output_format is not specified or not supported for saving
        save_format = output_format if output_format in Image.SAVE else original_format or 'PNG' 
        img.save(img_io, format=save_format)
        img_io.seek(0)
    except KeyError:
         return jsonify({'error': f'Unsupported output format: {output_format}. Supported formats include JPEG, PNG, GIF, BMP, TIFF, WEBP etc.'}), 400
    except Exception as e:
        return jsonify({'error': f'Error saving image: {str(e)}'}), 500

    mime_type_map = {
        'PNG': 'image/png',
        'JPEG': 'image/jpeg',
        'GIF': 'image/gif',
        'BMP': 'image/bmp',
        'TIFF': 'image/tiff',
        'WEBP': 'image/webp'
    }
    
    return send_file(img_io, mimetype=mime_type_map.get(save_format, 'application/octet-stream'), as_attachment=True, download_name=f'processed_image.{save_format.lower()}')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
