from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import qrcode
import io

app = Flask(__name__)
CORS(app)

@app.route('/python-qrcode/generate-qrcode', methods=['POST'])
def generate_qrcode_route():
    data = request.get_json()
    qr_data = data.get('data')
    version = data.get('version', 1)
    error_correction = data.get('error_correction', 'M').upper()
    box_size = data.get('box_size', 10)
    border = data.get('border', 4)
    fill_color = data.get('fill_color', 'black')
    back_color = data.get('back_color', 'white')
    image_format = data.get('format', 'png').lower()

    if not qr_data:
        return jsonify({'error': 'Data for QR code is required'}), 400

    error_correction_map = {
        'L': qrcode.constants.ERROR_CORRECT_L, # About 7% or less errors can be corrected.
        'M': qrcode.constants.ERROR_CORRECT_M, # About 15% or less errors can be corrected.
        'Q': qrcode.constants.ERROR_CORRECT_Q, # About 25% or less errors can be corrected.
        'H': qrcode.constants.ERROR_CORRECT_H  # About 30% or less errors can be corrected.
    }

    if error_correction not in error_correction_map:
        return jsonify({'error': 'Invalid error_correction level. Choose from L, M, Q, H.'}), 400

    try:
        qr = qrcode.QRCode(
            version=version,
            error_correction=error_correction_map[error_correction],
            box_size=box_size,
            border=border,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        img_io = io.BytesIO()
        if image_format == 'png':
            img.save(img_io, 'PNG')
            mimetype = 'image/png'
        elif image_format == 'jpeg':
            img.save(img_io, 'JPEG')
            mimetype = 'image/jpeg'
        # Add other formats if qrcode library supports them directly or via Pillow
        else:
            return jsonify({'error': 'Unsupported image format. Choose png or jpeg.'}), 400
        img_io.seek(0)

        return send_file(img_io, mimetype=mimetype, as_attachment=True, download_name=f'qrcode.{image_format}')

    except ValueError as ve:
        return jsonify({'error': f'Invalid parameter: {str(ve)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error generating QR code: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True, port=5003)
