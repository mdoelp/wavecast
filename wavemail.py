import requests
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime, UTC

# ============================================
# SETTINGS
# ============================================

LAT = 43
LON = -70.25  # Boston Harbor entrance

FORECAST_HOURS = range(0, 240, 3)

# ============================================
# DATE
# ============================================

today = datetime.now(UTC)

date_str = today.strftime("%Y%m%d")

# NOAA uses 0-360 longitude
target_lon = LON % 360

wave_heights_ft = []
forecast_times = []

# ============================================
# LOOP THROUGH FORECAST FILES
# ============================================

for fhour in FORECAST_HOURS:

    filename = f"wave_f{fhour:03d}.grib2"

    url = (
        f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/"
        f"gfs/prod/gfs.{date_str}/00/wave/gridded/"
        f"gfswave.t00z.atlocn.0p16.f{fhour:03d}.grib2"
    )

    print(f"Downloading forecast hour {fhour}")

    r = requests.get(url)

    if r.status_code != 200:
        print(f"Skipping f{fhour:03d}")
        continue

    with open(filename, "wb") as f:
        f.write(r.content)

    try:
        ds = xr.open_dataset(
            filename,
            engine="cfgrib"
        )

        # Extract significant wave height
        point = ds["swh"].sel(
            latitude=LAT,
            longitude=target_lon,
            method="nearest"
        )

        wave_m = float(point.values)

        wave_ft = wave_m * 3.28084

        forecast_time = (
            today +
            pd.Timedelta(hours=fhour)
        )

        forecast_times.append(forecast_time)
        wave_heights_ft.append(wave_ft)

        print(
            f"Hour {fhour}: "
            f"{wave_ft:.1f} ft"
        )

    except Exception as e:
        print(f"Error reading f{fhour:03d}:")
        print(e)

# ============================================
# DATAFRAME
# ============================================

df = pd.DataFrame({
    "Forecast Time": forecast_times,
    "Wave Height (ft)": wave_heights_ft
})

print(df.head())

# ============================================
# PLOT
# ============================================

plt.figure(figsize=(12,6))

plt.plot(
    df["Forecast Time"],
    df["Wave Height (ft)"],
    marker="o",
    linewidth=2
)

plt.title(
    "NOAA Significant Wave Height Forecast\nBoston Harbor Entrance"
)

plt.xlabel("Forecast Time")
plt.ylabel("Wave Height (ft)")

plt.grid(True)

plt.tight_layout()

print("Saving PNG...")

plt.savefig(
    "BostonHarborWaveForecast.png",
    dpi=300,
    bbox_inches="tight"
)

print("PNG saved")

print("Saving CSV...")

df.to_csv(
    "BostonHarborWaveForecast.csv",
    index=False
)

print("CSV saved")

# ============================================
# EMAIL FORECAST
# ============================================

import smtplib
from email.message import EmailMessage

EMAIL_FROM = "mbdoelp@gmail.com"
EMAIL_TO = "mbdoelp@gmail.com"

APP_PASSWORD = "wadg uuae brwh shrd"

print("Preparing email...")

msg = EmailMessage()

msg["Subject"] = "Boston Harbor Wave Forecast"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

body = (
    "Boston Harbor Wave Forecast\n\n"
    f"Location:\n"
    f"Latitude: {LAT}\n"
    f"Longitude: {LON}\n\n"
    "Forecast:\n\n"
    + df.to_string(index=False)
)

msg.set_content(body)

print("Attaching PNG...")

with open(
    "BostonHarborWaveForecast.png",
    "rb"
) as f:

    msg.add_attachment(
        f.read(),
        maintype="image",
        subtype="png",
        filename="BostonHarborWaveForecast.png"
    )

print("PNG attached")

print("Attaching CSV...")

with open(
    "BostonHarborWaveForecast.csv",
    "rb"
) as f:

    msg.add_attachment(
        f.read(),
        maintype="text",
        subtype="csv",
        filename="BostonHarborWaveForecast.csv"
    )

print("CSV attached")

# ============================================
# SEND EMAIL
# ============================================

try:

    print("Connecting to Gmail server...")

    with smtplib.SMTP(
        "smtp.gmail.com",
        587,
        timeout=30
    ) as server:

        print("Starting TLS...")

        server.starttls()

        print("Logging into Gmail...")

        server.login(
            EMAIL_FROM,
            APP_PASSWORD
        )

        print("Sending message...")

        server.send_message(msg)

        print("Message sent successfully!")

except Exception as e:

    print("\nEMAIL ERROR:")
    print(type(e))
    print(e)
