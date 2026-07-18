import json
import datetime
import os
import tkinter as tk
from tkinter import filedialog
from collections import Counter


# Palauttaa vuosiluvun Spotifyn aikaleimasta
def get_year(timestamp):
    date_object = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return date_object.year


# Palauttaa kuukauden Spotifyn aikaleimasta
def get_month(timestamp):
    date_object = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return date_object.month


# Näyttää numerovalikon ja palauttaa käyttäjän valinnan
def show_menu(title, options):
    print(f"\n{title}")
    print("-" * len(title))
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")

    while True:
        try:
            choice = int(input("\nValinta: ").strip())
            if 1 <= choice <= len(options):
                return choice
            print(f"Syötä numero väliltä 1-{len(options)}.")
        except ValueError:
            print(f"Syötä numero väliltä 1-{len(options)}.")


# Tallentaa tulokset tiedostoon. Jos tiedosto on jo olemassa, lisätään numero nimen perään
def save_results_to_file(content, filename):
    base_filename, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while os.path.exists(new_filename):
        new_filename = f"{base_filename}_{counter}{extension}"
        counter += 1

    try:
        with open(new_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Tulokset on tallennettu tiedostoon: {new_filename}")
    except OSError as e:
        print(f"Tiedoston tallentaminen epäonnistui: {e}")


# Tarkistaa, onko aikaleima oikeassa muodossa
def is_valid_timestamp(ts):
    try:
        datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except (ValueError, TypeError):
        return False


# Tarkistaa, onko tiedosto validi Spotify JSON-tiedosto.
# Käy läpi kaikki objektit ja varmistaa, että vaaditut kentät löytyvät
# ja että aikaleima on oikeassa muodossa.
# Palauttaa (True, "") jos validi, tai (False, virheilmoitus) jos ei.
def is_valid_spotify_json(file_path):
    required_keys = [
        "ts",
        "master_metadata_album_artist_name",
        "master_metadata_track_name",
        "platform"
    ]

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        if not isinstance(data, list):
            return False, "Tiedoston sisältö ei ole lista."

        if len(data) == 0:
            return False, "Tiedosto on tyhjä."

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                return False, f"Objekti {i+1} ei ole oikeaa muotoa."

            missing_fields = [key for key in required_keys if key not in item]
            if missing_fields:
                return False, (
                    f"Objektista {i+1} puuttuu kenttä/kenttiä: "
                    f"{', '.join(missing_fields)}"
                )

            if not is_valid_timestamp(item["ts"]):
                return False, (
                    f"Objektin {i+1} aikaleima '{item['ts']}' "
                    f"ei ole oikeassa muodossa (vaaditaan YYYY-MM-DDTHH:MM:SSZ)."
                )

        return True, ""

    except json.JSONDecodeError as e:
        return False, f"Tiedosto ei ole validi JSON: {e}"
    except OSError as e:
        return False, f"Tiedostoa ei voitu avata: {e}"
    except (ValueError, TypeError) as e:
        return False, f"Tiedoston lukeminen epäonnistui: {e}"


# Avaa kansionvalintaikkunan ja palauttaa valitun kansion polun
def select_folder_with_dialog():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    folder_path = filedialog.askdirectory(
        title="Valitse kansio, jossa Spotify JSON-tiedostot sijaitsevat"
    )

    root.destroy()
    return folder_path


# Käy läpi kansion kaikki JSON-tiedostot, validoi ne ja yhdistää datan yhdeksi listaksi.
# Palauttaa (data, ladatut_tiedostot, ohitetut_tiedostot).
def load_spotify_data_from_folder(folder_path):
    all_data = []
    loaded = []
    skipped = []

    json_files = sorted(
        [f for f in os.listdir(folder_path) if f.endswith('.json')]
    )

    if not json_files:
        return [], [], []

    for file in json_files:
        path = os.path.join(folder_path, file)
        valid, error_message = is_valid_spotify_json(path)

        if valid:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            all_data.extend(data)
            loaded.append(file)
        else:
            skipped.append((file, error_message))

    return all_data, loaded, skipped


# Kysyy tiedostonimen ja avaa kansionvalintaikkunan tallennusta varten.
# Tiedostot tallennetaan .txt-muodossa.
def ask_save(output):
    while True:
        file_name = input("Anna tallennettavan tiedoston nimi (ilman tiedostopäätettä):\n").strip()
        if file_name:
            break
        print("Tiedostonimi ei voi olla tyhjä.")

    # Avataan kansionvalintaikkuna tallennuspaikan valintaan
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory(title="Valitse kansio johon tiedosto tallennetaan")
    root.destroy()

    if not folder:
        print("Kansiota ei valittu, tallentaminen peruutettu.")
        return

    full_path = os.path.join(folder, file_name + ".txt")
    save_results_to_file(output, full_path)
    print(f"Tiedosto tallennettu kansioon: {folder}")


# Hakee laulut datasta annetun vuoden perusteella ja suodattaa duplikaatit
def get_songs(data, listen_year):
    found_songs = False
    output = ""
    seen_songs = set()

    for song in data:
        if get_year(song["ts"]) == listen_year or listen_year == 0:
            artist = song["master_metadata_album_artist_name"]
            track = song["master_metadata_track_name"]

            if artist is None and track is None:
                continue

            # Suodatetaan duplikaatit artisti+kappale-yhdistelmän perusteella
            song_key = (artist, track)
            if song_key in seen_songs:
                continue
            seen_songs.add(song_key)

            found_songs = True
            year = get_year(song["ts"])
            device = song["platform"]
            output += f"\n{artist}: {track}, kuunneltu vuonna {year} laitteelta {device}\n"

    return found_songs, output


# Näyttää ensin valikon datassa esiintyvistä vuosista, sitten kuukausista.
# Palauttaa (vuosi, kuukausi) tai None jos käyttäjä peruuttaa.
def select_year_and_month(data):
    MONTH_NAMES = {
        1: "Tammikuu", 2: "Helmikuu", 3: "Maaliskuu", 4: "Huhtikuu",
        5: "Toukokuu", 6: "Kesäkuu", 7: "Heinäkuu", 8: "Elokuu",
        9: "Syyskuu", 10: "Lokakuu", 11: "Marraskuu", 12: "Joulukuu"
    }

    # Kerätään kaikki vuosi+kuukausi-yhdistelmät datasta
    available = sorted(set(
        (get_year(song["ts"]), get_month(song["ts"]))
        for song in data
        if song["master_metadata_track_name"] is not None
    ))

    years = sorted(set(y for y, m in available))
    year_options = [str(y) for y in years] + ["Peruuta"]
    year_choice = show_menu("Valitse vuosi", year_options)

    if year_choice == len(year_options):
        return None

    selected_year = years[year_choice - 1]

    months = sorted(set(m for y, m in available if y == selected_year))
    month_options = [MONTH_NAMES[m] for m in months] + ["Peruuta"]
    month_choice = show_menu(f"Valitse kuukausi ({selected_year})", month_options)

    if month_choice == len(month_options):
        return None

    selected_month = months[month_choice - 1]

    return selected_year, selected_month


# Laskee kuunnelluimmat kappaleet annetulle vuodelle.
# Palauttaa (output, löydettiinkö tuloksia).
def get_top_songs_for_year(data, year, limit):
    # Lasketaan kuuntelumäärät artisti+kappale-yhdistelmittäin
    play_counts = Counter()

    for song in data:
        if get_year(song["ts"]) != year:
            continue

        artist = song["master_metadata_album_artist_name"]
        track = song["master_metadata_track_name"]

        if artist is None or track is None:
            continue

        play_counts[(artist, track)] += 1

    if not play_counts:
        return "", False

    output = f"\nTop {limit} kuunnelluimmat — {year}\n"
    output += "-" * len(output.strip()) + "\n"

    for i, ((artist, track), count) in enumerate(play_counts.most_common(limit), 1):
        output += f"  {i}. {artist}: {track} ({count} kertaa)\n"

    return output, True


# Laskee kuunnelluimmat kappaleet annetulle vuodelle ja kuukaudelle.
# Palauttaa (output, löydettiinkö tuloksia).
def get_top_songs_for_month(data, year, month, limit):
    MONTH_NAMES = {
        1: "Tammikuu", 2: "Helmikuu", 3: "Maaliskuu", 4: "Huhtikuu",
        5: "Toukokuu", 6: "Kesäkuu", 7: "Heinäkuu", 8: "Elokuu",
        9: "Syyskuu", 10: "Lokakuu", 11: "Marraskuu", 12: "Joulukuu"
    }

    # Lasketaan kuuntelumäärät artisti+kappale-yhdistelmittäin
    play_counts = Counter()

    for song in data:
        if get_year(song["ts"]) != year or get_month(song["ts"]) != month:
            continue

        artist = song["master_metadata_album_artist_name"]
        track = song["master_metadata_track_name"]

        if artist is None or track is None:
            continue

        play_counts[(artist, track)] += 1

    if not play_counts:
        return "", False

    month_name = MONTH_NAMES[month]
    output = f"\nTop {limit} kuunnelluimmat — {month_name} {year}\n"
    output += "-" * len(output.strip()) + "\n"

    for i, ((artist, track), count) in enumerate(play_counts.most_common(limit), 1):
        output += f"  {i}. {artist}: {track} ({count} kertaa)\n"

    return output, True


# Hakee kappaleita tai artisteja hakusanan perusteella (osittainen, kirjainkoosta riippumaton).
# Näyttää kuuntelumäärän sekä ensimmäisen ja viimeisimmän kuuntelukerran.
# Palauttaa (output, löydettiinkö tuloksia).
def free_search(data, query, search_by):
    query_lower = query.lower()

    # Tallennetaan jokaiselle kappaleelle kuuntelumäärä ja aikaleimalista
    play_counts = Counter()
    timestamps = {}

    for song in data:
        artist = song["master_metadata_album_artist_name"]
        track = song["master_metadata_track_name"]

        if artist is None or track is None:
            continue

        # Tarkistetaan osuuko hakusana artistiin tai kappaleeseen
        if search_by == "artist" and query_lower not in artist.lower():
            continue
        if search_by == "track" and query_lower not in track.lower():
            continue

        key = (artist, track)
        play_counts[key] += 1

        ts = datetime.datetime.strptime(song["ts"], "%Y-%m-%dT%H:%M:%SZ")
        if key not in timestamps:
            timestamps[key] = [ts, ts]
        else:
            if ts < timestamps[key][0]:
                timestamps[key][0] = ts
            if ts > timestamps[key][1]:
                timestamps[key][1] = ts

    if not play_counts:
        return "", False

    output = f"\nHakutulokset: \"{query}\"\n"
    output += "-" * len(output.strip()) + "\n"

    for (artist, track), count in sorted(play_counts.items(), key=lambda x: x[1], reverse=True):
        first = timestamps[(artist, track)][0].strftime("%d.%m.%Y")
        last = timestamps[(artist, track)][1].strftime("%d.%m.%Y")
        output += f"  {artist}: {track} ({count} kertaa)\n"
        output += f"    Ensin kuunneltu: {first} — Viimeksi: {last}\n"

    return output, True


# Laskee ja muodostaa wrapped-yhteenvedon annetulle vuodelle.
# Palauttaa (output, löydettiinkö dataa).
def generate_wrapped(data, year):
    MONTH_NAMES = {
        1: "Tammikuu", 2: "Helmikuu", 3: "Maaliskuu", 4: "Huhtikuu",
        5: "Toukokuu", 6: "Kesäkuu", 7: "Heinäkuu", 8: "Elokuu",
        9: "Syyskuu", 10: "Lokakuu", 11: "Marraskuu", 12: "Joulukuu"
    }

    track_counts = Counter()
    artist_counts = Counter()
    month_counts = Counter()
    first_heard = {}
    total_ms = 0
    has_ms_played = False

    for song in data:
        if get_year(song["ts"]) != year:
            continue

        artist = song["master_metadata_album_artist_name"]
        track = song["master_metadata_track_name"]

        if artist is None or track is None:
            continue

        track_counts[(artist, track)] += 1
        artist_counts[artist] += 1
        month_counts[get_month(song["ts"])] += 1

        # Tallennetaan ensikuunteluaika per kappale
        ts = datetime.datetime.strptime(song["ts"], "%Y-%m-%dT%H:%M:%SZ")
        key = (artist, track)
        if key not in first_heard or ts < first_heard[key]:
            first_heard[key] = ts

        # Lasketaan kuunteluaika jos ms_played löytyy
        if "ms_played" in song and song["ms_played"] is not None:
            total_ms += song["ms_played"]
            has_ms_played = True

    if not track_counts:
        return "", False

    # Uusin löytö = kappale joka on kuunneltu ensimmäistä kertaa viimeisimpänä
    newest_discovery = max(first_heard.items(), key=lambda x: x[1])
    newest_artist, newest_track = newest_discovery[0]
    newest_date = newest_discovery[1].strftime("%d.%m.%Y")

    # Kuunneluin kuukausi
    top_month_num, top_month_count = month_counts.most_common(1)[0]
    top_month_name = MONTH_NAMES[top_month_num]

    separator = "=" * 40

    output = f"""
{separator}
       SPOTIFY WRAPPED {year}
{separator}

🎵 TOP 5 KAPPALEET
"""
    for i, ((artist, track), count) in enumerate(track_counts.most_common(5), 1):
        output += f"  {i}. {artist}: {track} ({count} kertaa)\n"

    output += f"""
🎤 TOP 5 ARTISTIT
"""
    for i, (artist, count) in enumerate(artist_counts.most_common(5), 1):
        output += f"  {i}. {artist} ({count} kuuntelua)\n"

    output += f"""
📅 KUUNNELUIN KUUKAUSI
  {top_month_name} — {top_month_count} kuuntelua

✨ UUSIN LÖYTÖ
  {newest_artist}: {newest_track}
  (Kuunneltu ensimmäistä kertaa {newest_date})
"""

    if has_ms_played:
        total_minutes = total_ms // 60000
        formatted_minutes = f"{total_minutes:,}".replace(",", " ")
        output += f"""
⏱️  KUUNTELUAIKA YHTEENSÄ
  {formatted_minutes} minuuttia
"""

    output += f"\n{separator}\n"

    return output, True


def main():
    print("\n--- Spotify Data Reader v.2.0 ---")

    data = []

    while True:
        # Päävalikko, näytetään kun dataa ei ole ladattu
        if not data:
            choice = show_menu("Päävalikko", [
                "Valitse kansio",
                "Lopeta"
            ])

            if choice == 1:
                folder_path = select_folder_with_dialog()

                if not folder_path:
                    print("Kansiota ei valittu.")
                    continue

                print(f"Valittu kansio: {folder_path}")
                print("Ladataan tiedostoja...")

                data, loaded, skipped = load_spotify_data_from_folder(folder_path)

                if loaded:
                    print(f"\nLadattu {len(loaded)} tiedostoa:")
                    for t in loaded:
                        print(f"  ✓ {t}")
                if skipped:
                    print(f"\nOhitettu {len(skipped)} tiedostoa (ei yhteensopiva Spotify-data):")
                    for t, reason in skipped:
                        print(f"  ✗ {t}: {reason}")

                if not data:
                    print("\nKansiosta ei löytynyt yhtään yhteensopivaa Spotify JSON-tiedostoa.")
                    data = []
                    continue

                print(f"\nYhteensä {len(data)} merkintää kaikista tiedostoista.")

            elif choice == 2:
                print("Näkemiin!")
                break

        # Hakuvalikko
        else:
            choice = show_menu("Mitä haetaan?", [
                "Hae vuoden mukaan",
                "Vuoden kuunnelluimmat",
                "Kuukauden kuunnelluimmat",
                "Vapaa haku",
                "Wrapped",
                "Vaihda kansiota",
                "Lopeta"
            ])

            if choice == 1:
                # Vuosihaku — silmukka jossa voi hakea uudella vuodella
                while True:
                    try:
                        listen_year = int(input("\nAnna haluttu vuosi (0 = kaikki vuodet):\n").strip())
                    except ValueError:
                        print("Et syöttänyt lukua. Yritä uudelleen.")
                        continue

                    found_songs, output = get_songs(data, listen_year)

                    if not found_songs:
                        year_text = "kaikilta vuosilta" if listen_year == 0 else f"vuodelta {listen_year}"
                        print(f"Hakutuloksia ei löytynyt {year_text}.")
                    else:
                        print(output)

                    action = show_menu("Mitä seuraavaksi?", [
                        "Tallenna tulokset",
                        "Hae uudella vuodella",
                        "Palaa hakuvalikkoon"
                    ])
                    if action == 1:
                        if found_songs:
                            ask_save(output)
                        else:
                            print("Ei tallennettavia tuloksia.")
                    elif action == 2:
                        continue
                    elif action == 3:
                        break

            elif choice == 2:
                # Vuoden kuunnelluimmat — silmukka jossa voi hakea toisella vuodella
                years = sorted(set(get_year(song["ts"]) for song in data if song["master_metadata_track_name"] is not None))

                while True:
                    year_options = [str(y) for y in years] + ["Peruuta"]
                    year_choice = show_menu("Valitse vuosi", year_options)

                    if year_choice == len(year_options):
                        break

                    selected_year = years[year_choice - 1]

                    while True:
                        try:
                            limit = int(input("\nKuinka monta kappaletta listataan?\n").strip())
                            if limit > 0:
                                break
                            print("Syötä positiivinen luku.")
                        except ValueError:
                            print("Et syöttänyt lukua. Yritä uudelleen.")

                    output, found = get_top_songs_for_year(data, selected_year, limit)

                    if not found:
                        print("Ei hakutuloksia valitulle vuodelle.")
                    else:
                        print(output)

                    action = show_menu("Mitä seuraavaksi?", [
                        "Tallenna tulokset",
                        "Hae toisella vuodella",
                        "Palaa hakuvalikkoon"
                    ])
                    if action == 1:
                        if found:
                            ask_save(output)
                        else:
                            print("Ei tallennettavia tuloksia.")
                    elif action == 2:
                        continue
                    elif action == 3:
                        break

            elif choice == 3:
                # Kuukauden kuunnelluimmat — silmukka jossa voi vaihtaa kuukautta tai vuotta
                while True:
                    result = select_year_and_month(data)
                    if result is None:
                        break

                    year, month = result

                    while True:
                        try:
                            limit = int(input("\nKuinka monta kappaletta listataan?\n").strip())
                            if limit > 0:
                                break
                            print("Syötä positiivinen luku.")
                        except ValueError:
                            print("Et syöttänyt lukua. Yritä uudelleen.")

                    output, found = get_top_songs_for_month(data, year, month, limit)

                    if not found:
                        print("Ei hakutuloksia valitulle kuukaudelle.")
                    else:
                        print(output)

                    action = show_menu("Mitä seuraavaksi?", [
                        "Tallenna tulokset",
                        "Hae toisella kuukaudella",
                        "Hae toisella vuodella",
                        "Palaa hakuvalikkoon"
                    ])
                    if action == 1:
                        if found:
                            ask_save(output)
                        else:
                            print("Ei tallennettavia tuloksia.")
                    elif action == 2:
                        # Palataan vuosivalikkoon mutta pysytään samassa vuodessa — näytetään vain kuukausivalikko
                        MONTH_NAMES = {
                            1: "Tammikuu", 2: "Helmikuu", 3: "Maaliskuu", 4: "Huhtikuu",
                            5: "Toukokuu", 6: "Kesäkuu", 7: "Heinäkuu", 8: "Elokuu",
                            9: "Syyskuu", 10: "Lokakuu", 11: "Marraskuu", 12: "Joulukuu"
                        }
                        available = sorted(set(
                            (get_year(song["ts"]), get_month(song["ts"]))
                            for song in data if song["master_metadata_track_name"] is not None
                        ))
                        months = sorted(set(m for y, m in available if y == year))
                        month_options = [MONTH_NAMES[m] for m in months] + ["Peruuta"]
                        month_choice = show_menu(f"Valitse kuukausi ({year})", month_options)
                        if month_choice == len(month_options):
                            break
                        month = months[month_choice - 1]
                        continue
                    elif action == 3:
                        continue
                    elif action == 4:
                        break

            elif choice == 4:
                # Vapaa haku — silmukka jossa voi hakea uudestaan tai vaihtaa artisti/kappale-valintaa
                search_type = show_menu("Hae artistin vai kappaleen mukaan?", [
                    "Artisti",
                    "Kappale"
                ])
                search_by = "artist" if search_type == 1 else "track"

                while True:
                    search_label = "artistia" if search_by == "artist" else "kappaletta"
                    query = input(f"\nSyötä hakusana ({search_label}):\n").strip()
                    if not query:
                        print("Hakusana ei voi olla tyhjä.")
                        continue

                    output, found = free_search(data, query, search_by)

                    if not found:
                        print(f"Hakusanalla \"{query}\" ei löytynyt tuloksia.")
                    else:
                        print(output)

                    action = show_menu("Mitä seuraavaksi?", [
                        "Tallenna tulokset",
                        "Hae uudestaan",
                        "Vaihda artisti/kappale-valinta",
                        "Palaa hakuvalikkoon"
                    ])
                    if action == 1:
                        if found:
                            ask_save(output)
                        else:
                            print("Ei tallennettavia tuloksia.")
                    elif action == 2:
                        continue
                    elif action == 3:
                        search_type = show_menu("Hae artistin vai kappaleen mukaan?", [
                            "Artisti",
                            "Kappale"
                        ])
                        search_by = "artist" if search_type == 1 else "track"
                        continue
                    elif action == 4:
                        break

            elif choice == 5:
                # Wrapped — valitaan vuosi ja näytetään yhteenveto
                years = sorted(set(get_year(song["ts"]) for song in data if song["master_metadata_track_name"] is not None))

                while True:
                    year_options = [str(y) for y in years] + ["Peruuta"]
                    year_choice = show_menu("Mille vuodelle tehdään wrapped?", year_options)

                    if year_choice == len(year_options):
                        break

                    selected_year = years[year_choice - 1]
                    output, found = generate_wrapped(data, selected_year)

                    if not found:
                        print("Ei dataa valitulle vuodelle.")
                    else:
                        print(output)

                    action = show_menu("Mitä seuraavaksi?", [
                        "Tallenna tulokset",
                        "Tee toiselle vuodelle",
                        "Palaa hakuvalikkoon"
                    ])
                    if action == 1:
                        if found:
                            ask_save(output)
                        else:
                            print("Ei tallennettavia tuloksia.")
                    elif action == 2:
                        continue
                    elif action == 3:
                        break

            elif choice == 6:
                data = []
                continue

            elif choice == 7:
                print("Näkemiin!")
                break


if __name__ == "__main__":
    main()