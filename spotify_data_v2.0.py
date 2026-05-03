import json
import datetime
import os
import tkinter as tk
from tkinter import filedialog


# Palauttaa vuosiluvun Spotifyn aikaleimasta
def get_year(timestamp):
    date_object = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return date_object.year


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

    with open(new_filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Tulokset on tallennettu tiedostoon: {new_filename}")


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


# Kysyy tiedostonimen ja avaa kansionvalintaikkunan tallennusta varten
# Tiedostot tallennetaan .txt -muodossa
def ask_save(output):
    file_name = input("Anna tallennettavan tiedoston nimi (ilman tiedostopäätettä):\n").strip()

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

        # Vuosihaku
        else:
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

            # Hakutulosvalikko
            choice = show_menu("Mitä seuraavaksi?", [
                "Hae uudella vuodella",
                "Tallenna tulokset tiedostoon",
                "Vaihda kansiota",
                "Lopeta"
            ])

            if choice == 1:
                continue
            elif choice == 2:
                if found_songs:
                    ask_save(output)
                else:
                    print("Ei tallennettavia tuloksia.")
            elif choice == 3:
                data = []
                continue
            elif choice == 4:
                print("Näkemiin!")
                break


if __name__ == "__main__":
    main()
