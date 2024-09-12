import json
import datetime
import os


# muunnetaan tällä funktiolla Spotifylta tuleva aikaleima helpommin luettavaan muotoon
def get_year(timestamp):
    date_object = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return date_object.year


def save_results_to_file(content, filename):
    """Tallentaa annetun sisällön tiedostoon. Luo uuden tiedostonimen, jos tiedosto on jo olemassa."""
    base_filename, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    # jos tiedostonimi on jo olemassa niin luodaan uusi tiedostonimi numerolla varustettuna
    while os.path.exists(new_filename):
        new_filename = f"{base_filename}_{counter}{extension}"
        counter += 1

    with open(new_filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Tulokset on tallennettu tiedostoon: {new_filename}")


while True:
    try:
        # Kysytään käyttäjältä kansion sijainti
        folder_path = input("Anna kansion sijainti: \n").replace('"', "")

        # Listataan JSON-tiedostot kansiosta
        print("Saatavilla olevat JSON-tiedostot:")
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        for i, file in enumerate(files, 1):
            print(f"{i}. {file}")

        # Kysytään käyttäjältä, mistä tiedostosta haetaan tiedot
        file_index = int(input("Anna valitsemasi tiedoston numero: \n")) - 1
        selected_file = os.path.join(folder_path, files[file_index])

        # haetaan tiedot valitusta json-tiedostosta ja lisätään se omaksi muuttujaksi
        with open(selected_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        while True:
            try:
                # kysytään käyttäjältä haluttua vuotta
                listen_year = int(input("Anna haluttu vuosi, jonka perusteella haetaan striimatut laulut "
                                        "(Luku 0 tulostaa kaikki vuodesta riippumatta.):\n").strip())

                # jotta ohjelma ei tulostaisi miljoonaa kertaa virheviestiä, otetaan vain toteutuneet arvot.
                found_songs = False
                output = ""  # Tallennetaan tulokset tähän muuttujaan

                for song in data:
                    # tarkistetaan ja tulostetaan tiedot vain, jos vuosi täsmää
                    if get_year(song["ts"]) == listen_year or listen_year == 0:
                        found_songs = True
                        artist = song["master_metadata_album_artist_name"]
                        track = song["master_metadata_track_name"]
                        year = get_year(song["ts"])
                        device = song["platform"]

                        # tarkistetaan, että artistin ja kappaleen nimet eivät ole None
                        if artist is None and track is None:
                            continue

                        # tallennetaan tulostettava rivi muuttujaan
                        output += f"\n{artist}: {track}, kuunneltu vuonna {year} laitteelta {device}\n"

                if not found_songs:
                    print(f"Vuodelta {listen_year} ei löytynyt hakutuloksia.")
                else:
                    print(output)
                    # kysytään käyttäjältä tallennetaanko tulokset tiedostoon
                    save_to_file = input("Haluatko tallentaa tulokset tiedostoon? (k/e):\n").lower().strip()
                    if save_to_file == "k":
                        file_name = input("Anna tallennettavan tiedoston nimi (ilman tiedostopäätettä):\n").strip()
                        save_results_to_file(output, file_name + ".txt")

                # kysytään käyttäjältä haluaako hän hakea toisella vuodella samasta tiedostosta
                another_year = input("Haluatko hakea toisella vuodella samasta tiedostosta? (k/e):\n").lower().strip()
                if another_year == "k":
                    continue
                else:
                    break

            # jos käyttäjä ei syötä lukua.
            except ValueError:
                print("Et syöttänyt lukua.\n")

        # annetaan käyttäjälle mahdollisuus hakea toisesta tiedostosta tietoja
        restart = input("Haluatko hakea tietoja toisesta tiedostosta? (k/e):\n").lower().strip()
        if restart == 'e':
            print("Näkemiin!")
            break
        elif restart == 'k':
            continue
        else:
            print("Vastaa joko k tai e!")

    # ilmoitetaan käyttäjälle, että kansion tai tiedoston polku oli väärä
    except (FileNotFoundError, OSError):
        print("Kansiota tai tiedostoa ei löydy. Onhan polku varmasti oikein?")

    restart = input("Haluatko yrittää uudelleen? (k/e):\n").lower().strip()

    if restart == 'e':
        print("Näkemiin!")
        break
    elif restart == 'k':
        continue
    else:
        print("Vastaa joko k tai e!")
