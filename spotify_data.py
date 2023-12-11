# lataathan songs.json tiedoston, jotta voit testata tiedoston polun kopiointia ja liittämistä ohjelmaan!
# 
import json
import datetime


# muunnetaan tällä funktiolla Spotifylta tuleva aikaleima helpommin luettavaan muotoon
def get_year(timestamp):
    date_object = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return date_object.year

try:
    # Jos windowsilla yrittää kopioida tiedoston sijaintia, niin tulee lainausmerkit mukaan.
    # käytetään replacea, jotta käyttäjän ei tarvitse erikseen siivota inputista lainausmerkkejä.
    filepath = input("Anna tiedoston sijainti: \n").replace('"', "")

    # haetaan tiedot json-tiedostosta ja lisätään se omaksi muuttujaksi
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)

        # kysytään käyttäjältä haluttua vuotta
        listen_year = int(input("Anna haluttu vuosi, jonka perusteella haetaan striimatut laulut:\n"))

        # jotta ohjelma ei tulostaisi miljoonaa kertaa virheviestiä, otetaan vain toteutuneet arvot.
        found_songs = False

        for song in data:
            # tarkistetaan ja tulostetaan tiedot vain, jos vuosi täsmää
            if get_year(song["ts"]) == listen_year:
                artist = song["master_metadata_album_artist_name"]
                track = song["master_metadata_track_name"]
                year = get_year(song["ts"])
                device = song["platform"]

                # tulostetaan yhdelle riville per dictionary
                print(f"{artist}: {track}, kuunneltu vuonna {year} laitteelta {device}")
                found_songs = True

        if not found_songs:
            print(f"Vuodelta {listen_year} ei löytynyt hakutuloksia.")

# ohjelma kaatui, kun sinne kirjotti mitä tahansa. Nyt ohjelma testaa, että tiedosto löytyy.
except FileNotFoundError:
    print("Tiedostoa ei löydy.")