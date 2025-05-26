from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from googlesearch import search  # pip install googlesearch-python

app = Flask(__name__)

@app.route('/')
def website():
    return render_template('index.html')


@app.route('/players/<player_name>', methods=['GET'])
def get_player(player_name):
    query = f"{player_name} cricbuzz"
    profile_link = None

    try:
        results = search(query, num_results=5)
        for link in results:
            if "cricbuzz.com/profiles/" in link:
                profile_link = link
                break
        if not profile_link:
            return jsonify({"error": "Player profile not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Google search failed: {str(e)}"}), 500

    try:
        page = requests.get(profile_link).text
        soup = BeautifulSoup(page, "lxml")

        profile = soup.find("div", id="playerProfile")
        pc = profile.find("div", class_="cb-col cb-col-100 cb-bg-white")

        name = pc.find("h1", class_="cb-font-40").text.strip()
        country = pc.find("h3", class_="cb-font-18 text-gray").text.strip()

        image_tag = pc.find("img")
        image_url = image_tag['src'] if image_tag else None

        personal = soup.find_all("div", class_="cb-col cb-col-60 cb-lst-itm-sm")
        role = personal[2].text.strip() if len(personal) > 2 else "N/A"

        icc = soup.find_all("div", class_="cb-col cb-col-25 cb-plyr-rank text-right")
        rankings = {
            "batting": {
                "test": icc[0].text.strip() if len(icc) > 0 else "N/A",
                "odi": icc[1].text.strip() if len(icc) > 1 else "N/A",
                "t20": icc[2].text.strip() if len(icc) > 2 else "N/A",
            },
            "bowling": {
                "test": icc[3].text.strip() if len(icc) > 3 else "N/A",
                "odi": icc[4].text.strip() if len(icc) > 4 else "N/A",
                "t20": icc[5].text.strip() if len(icc) > 5 else "N/A",
            },
        }

        summary = soup.find_all("div", class_="cb-plyr-tbl")
        batting_stats, bowling_stats = {}, {}

        if summary and len(summary) >= 2:
            # Batting
            bat_rows = summary[0].find("tbody").find_all("tr")
            for row in bat_rows:
                cols = row.find_all("td")
                if len(cols) >= 13:
                    fmt = cols[0].text.strip().lower()
                    batting_stats[fmt] = {
                        "matches": cols[1].text.strip(),
                        "runs": cols[3].text.strip(),
                        "highest_score": cols[5].text.strip(),
                        "average": cols[6].text.strip(),
                        "strike_rate": cols[7].text.strip(),
                        "hundreds": cols[12].text.strip(),
                        "fifties": cols[11].text.strip(),
                    }

            # Bowling
            bowl_rows = summary[1].find("tbody").find_all("tr")
            for row in bowl_rows:
                cols = row.find_all("td")
                if len(cols) >= 12:
                    fmt = cols[0].text.strip().lower()
                    bowling_stats[fmt] = {
                        "balls": cols[3].text.strip(),
                        "runs": cols[4].text.strip(),
                        "wickets": cols[5].text.strip(),
                        "best_bowling_innings": cols[9].text.strip(),
                        "economy": cols[7].text.strip(),
                        "five_wickets": cols[11].text.strip(),
                    }

        player_data = {
            "name": name,
            "country": country,
            "image": image_url,
            "role": role,
            "rankings": rankings,
            "batting_stats": batting_stats,
            "bowling_stats": bowling_stats,
        }

        return jsonify(player_data)

    except Exception as e:
        return jsonify({"error": f"Failed to extract player data: {str(e)}"}), 500


@app.route('/schedule')
def schedule():
    try:
        link = "https://www.cricbuzz.com/cricket-schedule/upcoming-series/international"
        source = requests.get(link).text
        soup = BeautifulSoup(source, "lxml")
        containers = soup.find_all("div", class_="cb-col-100 cb-col")
        matches = []

        for box in containers:
            date = box.find("div", class_="cb-lv-grn-strip text-bold")
            info = box.find("div", class_="cb-col-100 cb-col")
            if date and info:
                matches.append(f"{date.text.strip()} - {info.text.strip()}")

        return jsonify(matches)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch schedule: {str(e)}"}), 500


@app.route('/live')
def live_matches():
    try:
        link = "https://www.cricbuzz.com/cricket-match/live-scores"
        source = requests.get(link).text
        soup = BeautifulSoup(source, "lxml")

        container = soup.find("div", class_="cb-col cb-col-100 cb-bg-white")
        match_divs = container.find_all("div", class_="cb-scr-wll-chvrn cb-lv-scrs-col")
        live_matches = [m.text.strip() for m in match_divs]

        return jsonify(live_matches)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch live matches: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)
