from flask import Flask, render_template, request
import math
from datetime import datetime
import pytz
import folium
from flask import Flask, render_template
from flask_frozen import Freezer

app = Flask(__name__)
freezer = Freezer(app)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Use this line to generate static files
    freezer.freeze()


def calculate_solar_position(latitude, longitude, date_time):
    # Convert latitude and longitude to radians
    lat = math.radians(latitude)
    lon = math.radians(longitude)

    # Calculate day of year
    day_of_year = date_time.timetuple().tm_yday

    # Calculate equation of time
    b = (360 / 365) * (day_of_year - 81)
    eot = 9.87 * math.sin(2 * math.radians(b)) - 7.53 * math.cos(math.radians(b)) - 1.5 * math.sin(math.radians(b))

    # Calculate solar declination
    declination = math.radians(23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81))))

    # Calculate hour angle
    current_hour = date_time.hour + date_time.minute / 60
    time_offset = eot + 4 * longitude - 60 * -5  # Assuming EST timezone
    tst = current_hour * 60 + time_offset
    hour_angle = math.radians((tst / 4) - 180)

    # Calculate solar elevation angle
    sin_elevation = math.sin(lat) * math.sin(declination) + math.cos(lat) * math.cos(declination) * math.cos(hour_angle)
    elevation = math.degrees(math.asin(sin_elevation))

    # Calculate solar azimuth angle
    cos_azimuth = (math.sin(declination) * math.cos(lat) - math.cos(declination) * math.sin(lat) * math.cos(hour_angle)) / math.cos(math.radians(elevation))
    azimuth = math.degrees(math.acos(cos_azimuth))
    if hour_angle > 0:
        azimuth = 360 - azimuth

    return elevation, azimuth

@app.route('/', methods=['GET', 'POST'])
def index():
    map_html = None
    output = None
    if request.method == 'POST':
        try:
            latitude = float(request.form['latitude'])
            longitude = float(request.form['longitude'])
            area = float(request.form['area'])

            # Get current time
            date_time = datetime.now(pytz.UTC)

            # Calculate solar position
            elevation, azimuth = calculate_solar_position(latitude, longitude, date_time)

            # Estimate energy output
            panel_efficiency = 0.2  # 20% efficiency
            sunlight_hours = 2000  # Average sunlight hours per year
            energy_output = area * panel_efficiency * sunlight_hours

            # Generate map with marker
            map_ = folium.Map(location=[latitude, longitude], zoom_start=12)
            folium.Marker([latitude, longitude],
                          popup=f"Solar Panel Position<br>Elevation: {elevation:.2f}°<br>Azimuth: {azimuth:.2f}°").add_to(map_)
            map_html = map_._repr_html_()

            output = {
                'elevation': elevation,
                'azimuth': azimuth,
                'energy_output': energy_output,
            }
        except Exception as e:
            output = {'error': str(e)}

    return render_template('index.html', map_html=map_html, output=output)

if __name__ == '__main__':
    app.run(debug=True)