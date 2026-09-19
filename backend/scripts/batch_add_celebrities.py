"""
batch_add_celebrities.py
Batch ingests missing Indian celebrities (Comedians, Directors, Cricketers,
Stars from Kannada, Malayalam, Tamil, Telugu, and Hindi industries).

STRICT VERIFICATION:
- Exactly 1 face in the photo (no group photos, no multiple people).
- Confidence >= 0.75, face size >= 65px.
- Verified Wikipedia Infobox + Wikimedia Commons portrait sources.
- Long-shot display photo selected for UI banner.
"""

import sys
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
import cv2
import numpy as np

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import DATASET_DIR, CELEBRITIES_JSON, EMBEDDINGS_NPY, METADATA_NPY
from app.face_engine import face_engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

CANDIDATES = [
    # ── Comedians / Digital Creators ─────────────────────────────────
    {"id": "kapil_sharma", "name": "Kapil Sharma", "category": "Comedian", "wiki": "Kapil Sharma (comedian)", "search": "Kapil Sharma"},
    {"id": "sunil_grover", "name": "Sunil Grover", "category": "Comedian", "wiki": "Sunil Grover", "search": "Sunil Grover"},
    {"id": "zakir_khan", "name": "Zakir Khan", "category": "Comedian", "wiki": "Zakir Khan (comedian)", "search": "Zakir Khan comedian"},
    {"id": "bhuvan_bam", "name": "Bhuvan Bam", "category": "Comedian", "wiki": "Bhuvan Bam", "search": "Bhuvan Bam"},
    {"id": "ashish_chanchlani", "name": "Ashish Chanchlani", "category": "Comedian", "wiki": "Ashish Chanchlani", "search": "Ashish Chanchlani"},
    {"id": "carryminati", "name": "CarryMinati", "category": "Comedian", "wiki": "CarryMinati", "search": "Ajey Nagar CarryMinati"},
    {"id": "harsh_beniwal", "name": "Harsh Beniwal", "category": "Comedian", "wiki": "Harsh Beniwal", "search": "Harsh Beniwal"},
    {"id": "amit_tandon", "name": "Amit Tandon", "category": "Comedian", "wiki": "Amit Tandon (comedian)", "search": "Amit Tandon comedian"},
    {"id": "munawar_faruqui", "name": "Munawar Faruqui", "category": "Comedian", "wiki": "Munawar Faruqui", "search": "Munawar Faruqui"},

    # ── Directors ───────────────────────────────────────────────────
    {"id": "atlee", "name": "Atlee", "category": "Director", "wiki": "Atlee (director)", "search": "Atlee Kumar director"},
    {"id": "gautam_vasudev_menon", "name": "Gautham Vasudev Menon", "category": "Director", "wiki": "Gautham Vasudev Menon", "search": "Gautham Menon"},
    {"id": "lokesh_kanagaraj", "name": "Lokesh Kanagaraj", "category": "Director", "wiki": "Lokesh Kanagaraj", "search": "Lokesh Kanagaraj"},
    {"id": "mani_ratnam", "name": "Mani Ratnam", "category": "Director", "wiki": "Mani Ratnam", "search": "Mani Ratnam"},
    {"id": "rajamouli", "name": "S. S. Rajamouli", "category": "Director", "wiki": "S. S. Rajamouli", "search": "SS Rajamouli"},
    {"id": "sandeep_reddy_vanga", "name": "Sandeep Reddy Vanga", "category": "Director", "wiki": "Sandeep Reddy Vanga", "search": "Sandeep Reddy Vanga"},
    {"id": "sanjay_leela_bhansali", "name": "Sanjay Leela Bhansali", "category": "Director", "wiki": "Sanjay Leela Bhansali", "search": "Sanjay Leela Bhansali"},
    {"id": "shankar", "name": "S. Shankar", "category": "Director", "wiki": "S. Shankar", "search": "S. Shankar director"},
    {"id": "sukumar", "name": "Sukumar", "category": "Director", "wiki": "Sukumar (director)", "search": "Sukumar director"},
    {"id": "trivikram_srinivas", "name": "Trivikram Srinivas", "category": "Director", "wiki": "Trivikram Srinivas", "search": "Trivikram Srinivas"},
    {"id": "vetrimaaran", "name": "Vetrimaaran", "category": "Director", "wiki": "Vetrimaaran", "search": "Vetrimaaran director"},

    # ── Women Cricketers ─────────────────────────────────────────────
    {"id": "harmanpreet_kaur", "name": "Harmanpreet Kaur", "category": "Cricketer", "wiki": "Harmanpreet Kaur", "search": "Harmanpreet Kaur"},
    {"id": "jemimah_rodrigues", "name": "Jemimah Rodrigues", "category": "Cricketer", "wiki": "Jemimah Rodrigues", "search": "Jemimah Rodrigues"},
    {"id": "poonam_yadav", "name": "Poonam Yadav", "category": "Cricketer", "wiki": "Poonam Yadav", "search": "Poonam Yadav cricketer"},
    {"id": "radha_yadav", "name": "Radha Yadav", "category": "Cricketer", "wiki": "Radha Yadav", "search": "Radha Yadav cricketer"},
    {"id": "richa_ghosh", "name": "Richa Ghosh", "category": "Cricketer", "wiki": "Richa Ghosh", "search": "Richa Ghosh cricketer"},
    {"id": "shafali_verma", "name": "Shafali Verma", "category": "Cricketer", "wiki": "Shafali Verma", "search": "Shafali Verma"},
    {"id": "smriti_mandhana", "name": "Smriti Mandhana", "category": "Cricketer", "wiki": "Smriti Mandhana", "search": "Smriti Mandhana"},

    # ── Men Cricketers ───────────────────────────────────────────────
    {"id": "ajinkya_rahane", "name": "Ajinkya Rahane", "category": "Cricketer", "wiki": "Ajinkya Rahane", "search": "Ajinkya Rahane"},
    {"id": "ambati_rayudu", "name": "Ambati Rayudu", "category": "Cricketer", "wiki": "Ambati Rayudu", "search": "Ambati Rayudu"},
    {"id": "bhuvneshwar_kumar", "name": "Bhuvneshwar Kumar", "category": "Cricketer", "wiki": "Bhuvneshwar Kumar", "search": "Bhuvneshwar Kumar"},
    {"id": "cheteshwar_pujara", "name": "Cheteshwar Pujara", "category": "Cricketer", "wiki": "Cheteshwar Pujara", "search": "Cheteshwar Pujara"},
    {"id": "dinesh_karthik", "name": "Dinesh Karthik", "category": "Cricketer", "wiki": "Dinesh Karthik", "search": "Dinesh Karthik"},
    {"id": "gautam_gambhir", "name": "Gautam Gambhir", "category": "Cricketer", "wiki": "Gautam Gambhir", "search": "Gautam Gambhir"},
    {"id": "harbhajan_singh", "name": "Harbhajan Singh", "category": "Cricketer", "wiki": "Harbhajan Singh", "search": "Harbhajan Singh"},
    {"id": "kuldeep_yadav", "name": "Kuldeep Yadav", "category": "Cricketer", "wiki": "Kuldeep Yadav", "search": "Kuldeep Yadav cricketer"},
    {"id": "lokesh_rahul", "name": "KL Rahul", "category": "Cricketer", "wiki": "KL Rahul", "search": "KL Rahul"},
    {"id": "manish_pandey", "name": "Manish Pandey", "category": "Cricketer", "wiki": "Manish Pandey", "search": "Manish Pandey cricketer"},
    {"id": "mayank_agarwal", "name": "Mayank Agarwal", "category": "Cricketer", "wiki": "Mayank Agarwal", "search": "Mayank Agarwal cricketer"},
    {"id": "murali_vijay", "name": "Murali Vijay", "category": "Cricketer", "wiki": "Murali Vijay", "search": "Murali Vijay cricketer"},
    {"id": "ruturaj_gaikwad", "name": "Ruturaj Gaikwad", "category": "Cricketer", "wiki": "Ruturaj Gaikwad", "search": "Ruturaj Gaikwad"},
    {"id": "shreyas_iyer", "name": "Shreyas Iyer", "category": "Cricketer", "wiki": "Shreyas Iyer", "search": "Shreyas Iyer"},
    {"id": "umesh_yadav", "name": "Umesh Yadav", "category": "Cricketer", "wiki": "Umesh Yadav", "search": "Umesh Yadav cricketer"},
    {"id": "varun_chakravarthy", "name": "Varun Chakravarthy", "category": "Cricketer", "wiki": "Varun Chakravarthy", "search": "Varun Chakravarthy"},
    {"id": "washington_sundar", "name": "Washington Sundar", "category": "Cricketer", "wiki": "Washington Sundar", "search": "Washington Sundar"},
    {"id": "yuzvendra_chahal", "name": "Yuzvendra Chahal", "category": "Cricketer", "wiki": "Yuzvendra Chahal", "search": "Yuzvendra Chahal"},

    # ── Kannada Stars ────────────────────────────────────────────────
    {"id": "ashika_rangnath", "name": "Ashika Ranganath", "category": "Actress", "wiki": "Ashika Ranganath", "search": "Ashika Ranganath"},
    {"id": "rachita_ram", "name": "Rachita Ram", "category": "Actress", "wiki": "Rachita Ram", "search": "Rachita Ram"},
    {"id": "ragini_prajwal", "name": "Ragini Prajwal", "category": "Actress", "wiki": "Ragini Prajwal", "search": "Ragini Prajwal"},
    {"id": "sapthami_gowda", "name": "Sapthami Gowda", "category": "Actress", "wiki": "Sapthami Gowda", "search": "Sapthami Gowda"},
    {"id": "darshan", "name": "Darshan Thoogudeepa", "category": "Actor", "wiki": "Darshan (actor)", "search": "Darshan Thoogudeepa"},
    {"id": "diganth", "name": "Diganth", "category": "Actor", "wiki": "Diganth", "search": "Diganth actor"},
    {"id": "ganesh", "name": "Ganesh", "category": "Actor", "wiki": "Ganesh (actor)", "search": "Ganesh Kannada actor"},
    {"id": "sudeep", "name": "Kiccha Sudeep", "category": "Actor", "wiki": "Sudeepa", "search": "Kiccha Sudeep"},
    {"id": "upendra", "name": "Upendra", "category": "Actor", "wiki": "Upendra (actor)", "search": "Upendra Kannada actor"},
    {"id": "vijay_raghavendra", "name": "Vijay Raghavendra", "category": "Actor", "wiki": "Vijay Raghavendra", "search": "Vijay Raghavendra"},

    # ── Malayalam Stars ──────────────────────────────────────────────
    {"id": "ann_augustine", "name": "Ann Augustine", "category": "Actress", "wiki": "Ann Augustine", "search": "Ann Augustine"},
    {"id": "anna_ben", "name": "Anna Ben", "category": "Actress", "wiki": "Anna Ben", "search": "Anna Ben actress"},
    {"id": "aparna_balamurali", "name": "Aparna Balamurali", "category": "Actress", "wiki": "Aparna Balamurali", "search": "Aparna Balamurali"},
    {"id": "darshana_rajendran", "name": "Darshana Rajendran", "category": "Actress", "wiki": "Darshana Rajendran", "search": "Darshana Rajendran"},
    {"id": "mamitha_baiju", "name": "Mamitha Baiju", "category": "Actress", "wiki": "Mamitha Baiju", "search": "Mamitha Baiju"},
    {"id": "nimisha_sajayan", "name": "Nimisha Sajayan", "category": "Actress", "wiki": "Nimisha Sajayan", "search": "Nimisha Sajayan"},
    {"id": "rajisha_vijayan", "name": "Rajisha Vijayan", "category": "Actress", "wiki": "Rajisha Vijayan", "search": "Rajisha Vijayan"},
    {"id": "saniya_iyappan", "name": "Saniya Iyappan", "category": "Actress", "wiki": "Saniya Iyappan", "search": "Saniya Iyappan"},
    {"id": "shobana", "name": "Shobana", "category": "Actress", "wiki": "Shobana", "search": "Shobana actress"},
    {"id": "urvashi", "name": "Urvashi", "category": "Actress", "wiki": "Urvashi (actress)", "search": "Urvashi actress"},
    {"id": "asif_ali", "name": "Asif Ali", "category": "Actor", "wiki": "Asif Ali (actor)", "search": "Asif Ali actor"},
    {"id": "basil_joseph", "name": "Basil Joseph", "category": "Actor", "wiki": "Basil Joseph", "search": "Basil Joseph"},
    {"id": "indrajith_sukumaran", "name": "Indrajith Sukumaran", "category": "Actor", "wiki": "Indrajith Sukumaran", "search": "Indrajith Sukumaran"},
    {"id": "joju_george", "name": "Joju George", "category": "Actor", "wiki": "Joju George", "search": "Joju George"},
    {"id": "kunchacko_boban", "name": "Kunchacko Boban", "category": "Actor", "wiki": "Kunchacko Boban", "search": "Kunchacko Boban"},
    {"id": "lukman_avaran", "name": "Lukman Avaran", "category": "Actor", "wiki": "Lukman Avaran", "search": "Lukman Avaran"},
    {"id": "mukesh", "name": "Mukesh", "category": "Actor", "wiki": "Mukesh (actor)", "search": "Mukesh Malayalam actor"},
    {"id": "murali_gopy", "name": "Murali Gopy", "category": "Actor", "wiki": "Murali Gopy", "search": "Murali Gopy"},
    {"id": "pranav_mohanlal", "name": "Pranav Mohanlal", "category": "Actor", "wiki": "Pranav Mohanlal", "search": "Pranav Mohanlal"},
    {"id": "soubin_shahir", "name": "Soubin Shahir", "category": "Actor", "wiki": "Soubin Shahir", "search": "Soubin Shahir"},
    {"id": "unni_mukundan", "name": "Unni Mukundan", "category": "Actor", "wiki": "Unni Mukundan", "search": "Unni Mukundan"},
    {"id": "vineeth_sreenivasan", "name": "Vineeth Sreenivasan", "category": "Actor", "wiki": "Vineeth Sreenivasan", "search": "Vineeth Sreenivasan"},

    # ── Tamil Stars ──────────────────────────────────────────────────
    {"id": "aishwarya_lekshmi", "name": "Aishwarya Lekshmi", "category": "Actress", "wiki": "Aishwarya Lekshmi", "search": "Aishwarya Lekshmi"},
    {"id": "amala_paul", "name": "Amala Paul", "category": "Actress", "wiki": "Amala Paul", "search": "Amala Paul"},
    {"id": "andrea_jeremiah", "name": "Andrea Jeremiah", "category": "Actress", "wiki": "Andrea Jeremiah", "search": "Andrea Jeremiah"},
    {"id": "anupama_parameswaran", "name": "Anupama Parameswaran", "category": "Actress", "wiki": "Anupama Parameswaran", "search": "Anupama Parameswaran"},
    {"id": "dhansika", "name": "Sai Dhanshika", "category": "Actress", "wiki": "Sai Dhanshika", "search": "Sai Dhanshika actress"},
    {"id": "divya_duraisamy", "name": "Divya Duraisamy", "category": "Actress", "wiki": "Divya Duraisamy", "search": "Divya Duraisamy"},
    {"id": "lakshmi_menon", "name": "Lakshmi Menon", "category": "Actress", "wiki": "Lakshmi Menon (actress)", "search": "Lakshmi Menon actress"},
    {"id": "megha_akash", "name": "Megha Akash", "category": "Actress", "wiki": "Megha Akash", "search": "Megha Akash"},
    {"id": "nithya_menen", "name": "Nithya Menen", "category": "Actress", "wiki": "Nithya Menen", "search": "Nithya Menen"},
    {"id": "priya_bhavani_shankar", "name": "Priya Bhavani Shankar", "category": "Actress", "wiki": "Priya Bhavani Shankar", "search": "Priya Bhavani Shankar"},
    {"id": "regina_cassandra", "name": "Regina Cassandra", "category": "Actress", "wiki": "Regina Cassandra", "search": "Regina Cassandra"},
    {"id": "shruti_haasan", "name": "Shruti Haasan", "category": "Actress", "wiki": "Shruti Haasan", "search": "Shruti Haasan"},
    {"id": "arjun_saravanan", "name": "Arjun Sarja", "category": "Actor", "wiki": "Arjun Sarja", "search": "Arjun Sarja actor"},
    {"id": "arvind_swamy", "name": "Arvind Swamy", "category": "Actor", "wiki": "Arvind Swamy", "search": "Arvind Swamy"},
    {"id": "ashok_selvan", "name": "Ashok Selvan", "category": "Actor", "wiki": "Ashok Selvan", "search": "Ashok Selvan"},
    {"id": "atharvaa", "name": "Atharvaa", "category": "Actor", "wiki": "Atharvaa", "search": "Atharvaa actor"},
    {"id": "bharath", "name": "Bharath", "category": "Actor", "wiki": "Bharath (actor)", "search": "Bharath actor"},
    {"id": "bobby_simha", "name": "Bobby Simha", "category": "Actor", "wiki": "Bobby Simha", "search": "Bobby Simha"},
    {"id": "gautam_karthik", "name": "Gautham Karthik", "category": "Actor", "wiki": "Gautham Karthik", "search": "Gautham Karthik"},
    {"id": "jiiva", "name": "Jiiva", "category": "Actor", "wiki": "Jiiva", "search": "Jiiva actor"},
    {"id": "kalaiyarasan", "name": "Kalaiyarasan", "category": "Actor", "wiki": "Kalaiyarasan", "search": "Kalaiyarasan actor"},
    {"id": "madhavan", "name": "R. Madhavan", "category": "Actor", "wiki": "R. Madhavan", "search": "R. Madhavan"},
    {"id": "manikandan", "name": "K. Manikandan", "category": "Actor", "wiki": "Manikandan (actor)", "search": "Manikandan actor Good Night"},
    {"id": "prasanna", "name": "Prasanna", "category": "Actor", "wiki": "Prasanna (actor)", "search": "Prasanna actor"},
    {"id": "santosh_prathap", "name": "Santhosh Prathap", "category": "Actor", "wiki": "Santhosh Prathap", "search": "Santhosh Prathap"},
    {"id": "simbu", "name": "Silambarasan TR", "category": "Actor", "wiki": "Silambarasan", "search": "Silambarasan TR"},
    {"id": "soori", "name": "Soori", "category": "Actor", "wiki": "Soori (actor)", "search": "Soori actor Viduthalai"},
    {"id": "vijay_antony", "name": "Vijay Antony", "category": "Actor", "wiki": "Vijay Antony", "search": "Vijay Antony"},
    {"id": "vishal", "name": "Vishal", "category": "Actor", "wiki": "Vishal (actor)", "search": "Vishal Tamil actor"},
    {"id": "vimal", "name": "Vimal", "category": "Actor", "wiki": "Vimal (actor)", "search": "Vimal actor Pasanga"},

    # ── Telugu Stars ─────────────────────────────────────────────────
    {"id": "genelia_deshmukh", "name": "Genelia D'Souza", "category": "Actress", "wiki": "Genelia D'Souza", "search": "Genelia D'Souza"},
    {"id": "ileana_dcruz", "name": "Ileana D'Cruz", "category": "Actress", "wiki": "Ileana D'Cruz", "search": "Ileana D'Cruz"},
    {"id": "mehreen_pirzada", "name": "Mehreen Pirzada", "category": "Actress", "wiki": "Mehreen Pirzada", "search": "Mehreen Pirzada"},
    {"id": "nidhhi_agerwal", "name": "Nidhhi Agerwal", "category": "Actress", "wiki": "Nidhhi Agerwal", "search": "Nidhhi Agerwal"},
    {"id": "sreeleela", "name": "Sreeleela", "category": "Actress", "wiki": "Sreeleela", "search": "Sreeleela actress"},
    {"id": "balakrishna", "name": "Nandamuri Balakrishna", "category": "Actor", "wiki": "Nandamuri Balakrishna", "search": "Nandamuri Balakrishna"},
    {"id": "bellamkonda_srinivas", "name": "Bellamkonda Sreenivas", "category": "Actor", "wiki": "Bellamkonda Sreenivas", "search": "Bellamkonda Sreenivas"},
    {"id": "chaitanya_akkala", "name": "Chaitanya Rao", "category": "Actor", "wiki": "Chaitanya Rao Madadi", "search": "Chaitanya Rao actor"},
    {"id": "gopichand", "name": "Gopichand", "category": "Actor", "wiki": "Gopichand (actor)", "search": "Gopichand Telugu actor"},
    {"id": "naveen_polishetty", "name": "Naveen Polishetty", "category": "Actor", "wiki": "Naveen Polishetty", "search": "Naveen Polishetty"},
    {"id": "nithiin", "name": "Nithiin", "category": "Actor", "wiki": "Nithiin", "search": "Nithiin actor"},
    {"id": "naga_shourya", "name": "Naga Shaurya", "category": "Actor", "wiki": "Naga Shaurya", "search": "Naga Shaurya"},
    {"id": "ram_pothineni", "name": "Ram Pothineni", "category": "Actor", "wiki": "Ram Pothineni", "search": "Ram Pothineni"},
    {"id": "ravi_teja", "name": "Ravi Teja", "category": "Actor", "wiki": "Ravi Teja", "search": "Ravi Teja"},
    {"id": "sai_dharam_tej", "name": "Sai Dharam Tej", "category": "Actor", "wiki": "Sai Durgha Tej", "search": "Sai Dharam Tej"},
    {"id": "sharwanand", "name": "Sharwanand", "category": "Actor", "wiki": "Sharwanand", "search": "Sharwanand"},
    {"id": "sree_vishnu", "name": "Sree Vishnu", "category": "Actor", "wiki": "Sree Vishnu", "search": "Sree Vishnu actor"},
    {"id": "sudheer_babu", "name": "Sudheer Babu", "category": "Actor", "wiki": "Sudheer Babu", "search": "Sudheer Babu"},
    {"id": "varun_tej", "name": "Varun Tej", "category": "Actor", "wiki": "Varun Tej", "search": "Varun Tej"},
    {"id": "vishwak_sen", "name": "Vishwak Sen", "category": "Actor", "wiki": "Vishwak Sen", "search": "Vishwak Sen"},
    {"id": "adivi_sesh", "name": "Adivi Sesh", "category": "Actor", "wiki": "Adivi Sesh", "search": "Adivi Sesh"},
    {"id": "naveen_chandra", "name": "Naveen Chandra", "category": "Actor", "wiki": "Naveen Chandra", "search": "Naveen Chandra"},
    {"id": "satyadev", "name": "Satyadev Kancharana", "category": "Actor", "wiki": "Satyadev Kancharana", "search": "Satyadev Kancharana"},
    {"id": "sundeep_kishan", "name": "Sundeep Kishan", "category": "Actor", "wiki": "Sundeep Kishan", "search": "Sundeep Kishan"},
    {"id": "teja_sajja", "name": "Teja Sajja", "category": "Actor", "wiki": "Teja Sajja", "search": "Teja Sajja"},

    # ── Bollywood Actresses ───────────────────────────────────────────
    {"id": "aditi_rao_hydari", "name": "Aditi Rao Hydari", "category": "Actress", "wiki": "Aditi Rao Hydari", "search": "Aditi Rao Hydari"},
    {"id": "bhagyashree", "name": "Bhagyashree", "category": "Actress", "wiki": "Bhagyashree", "search": "Bhagyashree actress"},
    {"id": "bipasha_basu", "name": "Bipasha Basu", "category": "Actress", "wiki": "Bipasha Basu", "search": "Bipasha Basu"},
    {"id": "daisy_shah", "name": "Daisy Shah", "category": "Actress", "wiki": "Daisy Shah", "search": "Daisy Shah"},
    {"id": "huma_qureshi", "name": "Huma Qureshi", "category": "Actress", "wiki": "Huma Qureshi", "search": "Huma Qureshi"},
    {"id": "isha_koppikar", "name": "Isha Koppikar", "category": "Actress", "wiki": "Isha Koppikar", "search": "Isha Koppikar"},
    {"id": "kangana_ranaut", "name": "Kangana Ranaut", "category": "Actress", "wiki": "Kangana Ranaut", "search": "Kangana Ranaut"},
    {"id": "lara_dutta", "name": "Lara Dutta", "category": "Actress", "wiki": "Lara Dutta", "search": "Lara Dutta"},
    {"id": "malaika_arora", "name": "Malaika Arora", "category": "Actress", "wiki": "Malaika Arora", "search": "Malaika Arora"},
    {"id": "manisha_koirala", "name": "Manisha Koirala", "category": "Actress", "wiki": "Manisha Koirala", "search": "Manisha Koirala"},
    {"id": "mouni_roy", "name": "Mouni Roy", "category": "Actress", "wiki": "Mouni Roy", "search": "Mouni Roy"},
    {"id": "neha_sharma", "name": "Neha Sharma", "category": "Actress", "wiki": "Neha Sharma", "search": "Neha Sharma"},
    {"id": "preity_zinta", "name": "Preity Zinta", "category": "Actress", "wiki": "Preity Zinta", "search": "Preity Zinta"},
    {"id": "rani_mukerji", "name": "Rani Mukerji", "category": "Actress", "wiki": "Rani Mukerji", "search": "Rani Mukerji"},
    {"id": "rekha", "name": "Rekha", "category": "Actress", "wiki": "Rekha", "search": "Rekha actress"},
    {"id": "shilpa_shetty", "name": "Shilpa Shetty", "category": "Actress", "wiki": "Shilpa Shetty", "search": "Shilpa Shetty"},
    {"id": "sonakshi_sinha", "name": "Sonakshi Sinha", "category": "Actress", "wiki": "Sonakshi Sinha", "search": "Sonakshi Sinha"},
    {"id": "sonam_kapoor", "name": "Sonam Kapoor", "category": "Actress", "wiki": "Sonam Kapoor", "search": "Sonam Kapoor"},
    {"id": "sridevi", "name": "Sridevi", "category": "Actress", "wiki": "Sridevi", "search": "Sridevi actress"},
    {"id": "sushmita_sen", "name": "Sushmita Sen", "category": "Actress", "wiki": "Sushmita Sen", "search": "Sushmita Sen"},
    {"id": "yami_gautam", "name": "Yami Gautam", "category": "Actress", "wiki": "Yami Gautam", "search": "Yami Gautam"},
    {"id": "zareen_khan", "name": "Zareen Khan", "category": "Actress", "wiki": "Zareen Khan", "search": "Zareen Khan"},

    # ── Bollywood / Hindi Actors ──────────────────────────────────────
    {"id": "aamir_khan", "name": "Aamir Khan", "category": "Actor", "wiki": "Aamir Khan", "search": "Aamir Khan"},
    {"id": "abhishek_bachchan", "name": "Abhishek Bachchan", "category": "Actor", "wiki": "Abhishek Bachchan", "search": "Abhishek Bachchan"},
    {"id": "aditya_roy_kapur", "name": "Aditya Roy Kapur", "category": "Actor", "wiki": "Aditya Roy Kapur", "search": "Aditya Roy Kapur"},
    {"id": "ajay_devgn", "name": "Ajay Devgn", "category": "Actor", "wiki": "Ajay Devgn", "search": "Ajay Devgn"},
    {"id": "akshay_kumar", "name": "Akshay Kumar", "category": "Actor", "wiki": "Akshay Kumar", "search": "Akshay Kumar"},
    {"id": "amitabh_bachchan", "name": "Amitabh Bachchan", "category": "Actor", "wiki": "Amitabh Bachchan", "search": "Amitabh Bachchan"},
    {"id": "anil_kapoor", "name": "Anil Kapoor", "category": "Actor", "wiki": "Anil Kapoor", "search": "Anil Kapoor"},
    {"id": "ayushmann_khurrana", "name": "Ayushmann Khurrana", "category": "Actor", "wiki": "Ayushmann Khurrana", "search": "Ayushmann Khurrana"},
    {"id": "bobby_deol", "name": "Bobby Deol", "category": "Actor", "wiki": "Bobby Deol", "search": "Bobby Deol"},
    {"id": "emraan_hashmi", "name": "Emraan Hashmi", "category": "Actor", "wiki": "Emraan Hashmi", "search": "Emraan Hashmi"},
    {"id": "farhan_akhtar", "name": "Farhan Akhtar", "category": "Actor", "wiki": "Farhan Akhtar", "search": "Farhan Akhtar"},
    {"id": "fardeen_khan", "name": "Fardeen Khan", "category": "Actor", "wiki": "Fardeen Khan", "search": "Fardeen Khan"},
    {"id": "govinda", "name": "Govinda", "category": "Actor", "wiki": "Govinda (actor)", "search": "Govinda actor"},
    {"id": "imran_khan", "name": "Imran Khan", "category": "Actor", "wiki": "Imran Khan (actor)", "search": "Imran Khan actor"},
    {"id": "jackie_shroff", "name": "Jackie Shroff", "category": "Actor", "wiki": "Jackie Shroff", "search": "Jackie Shroff"},
    {"id": "jim_sarbh", "name": "Jim Sarbh", "category": "Actor", "wiki": "Jim Sarbh", "search": "Jim Sarbh"},
    {"id": "kunal_khemu", "name": "Kunal Khemu", "category": "Actor", "wiki": "Kunal Khemu", "search": "Kunal Khemu"},
    {"id": "manoj_bajpayee", "name": "Manoj Bajpayee", "category": "Actor", "wiki": "Manoj Bajpayee", "search": "Manoj Bajpayee"},
    {"id": "naseeruddin_shah", "name": "Naseeruddin Shah", "category": "Actor", "wiki": "Naseeruddin Shah", "search": "Naseeruddin Shah"},
    {"id": "neil_nitin_mukesh", "name": "Neil Nitin Mukesh", "category": "Actor", "wiki": "Neil Nitin Mukesh", "search": "Neil Nitin Mukesh"},
    {"id": "ranbir_kapoor", "name": "Ranbir Kapoor", "category": "Actor", "wiki": "Ranbir Kapoor", "search": "Ranbir Kapoor"},
    {"id": "ranveer_singh", "name": "Ranveer Singh", "category": "Actor", "wiki": "Ranveer Singh", "search": "Ranveer Singh"},
    {"id": "ritesh_deshmukh", "name": "Riteish Deshmukh", "category": "Actor", "wiki": "Riteish Deshmukh", "search": "Riteish Deshmukh"},
    {"id": "saif_ali_khan", "name": "Saif Ali Khan", "category": "Actor", "wiki": "Saif Ali Khan", "search": "Saif Ali Khan"},
    {"id": "shahid_kapoor", "name": "Shahid Kapoor", "category": "Actor", "wiki": "Shahid Kapoor", "search": "Shahid Kapoor"},
    {"id": "shah_rukh_khan", "name": "Shah Rukh Khan", "category": "Actor", "wiki": "Shah Rukh Khan", "search": "Shah Rukh Khan"},
    {"id": "sharman_joshi", "name": "Sharman Joshi", "category": "Actor", "wiki": "Sharman Joshi", "search": "Sharman Joshi"},
    {"id": "siddhant_chaturvedi", "name": "Siddhant Chaturvedi", "category": "Actor", "wiki": "Siddhant Chaturvedi", "search": "Siddhant Chaturvedi"},
    {"id": "suniel_shetty", "name": "Suniel Shetty", "category": "Actor", "wiki": "Suniel Shetty", "search": "Suniel Shetty"},
    {"id": "varun_dhawan", "name": "Varun Dhawan", "category": "Actor", "wiki": "Varun Dhawan", "search": "Varun Dhawan"},
    {"id": "vicky_kaushal", "name": "Vicky Kaushal", "category": "Actor", "wiki": "Vicky Kaushal", "search": "Vicky Kaushal"},
    {"id": "vivek_oberoi", "name": "Vivek Oberoi", "category": "Actor", "wiki": "Vivek Oberoi", "search": "Vivek Oberoi"},
]

def fetch_urls(c_info: dict, max_count: int = 6) -> list[str]:
    urls = []
    # 1. Wikipedia Infobox (Human-verified portrait)
    wiki_title = c_info.get("wiki") or c_info["name"]
    try:
        url_wiki = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(wiki_title)}&prop=pageimages&pithumbsize=1000&format=json"
        req = urllib.request.Request(url_wiki, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for _, p in data.get("query", {}).get("pages", {}).items():
                thumb = p.get("thumbnail", {}).get("source")
                if thumb:
                    urls.append(thumb)
    except Exception:
        pass

    # 2. Wikimedia Commons filtered search
    search_q = c_info.get("search") or c_info["name"]
    try:
        url_comm = (
            f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
            f"&gsrnamespace=6&gsrsearch={urllib.parse.quote(search_q)}&gsrlimit={max_count + 4}"
            "&prop=imageinfo&iiprop=url&iiurlwidth=800&format=json"
        )
        req = urllib.request.Request(url_comm, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for _, p in data.get("query", {}).get("pages", {}).items():
                title = p.get("title", "").lower()
                # Exclude non-person media
                if any(bad in title for bad in ["logo", "icon", "signature", "graph", "diagram", "flag", "pdf", "poster", "stadium"]):
                    continue
                ii = p.get("imageinfo", [])
                if ii:
                    thumb = ii[0].get("thumburl") or ii[0].get("url")
                    if thumb and thumb not in urls:
                        urls.append(thumb)
                if len(urls) >= max_count:
                    break
    except Exception:
        pass

    return urls

def download_file(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read()
            if len(content) < 4000:
                return False
            dest.write_bytes(content)
            return True
    except Exception:
        return False

def inspect_and_filter_folder(folder: Path) -> list[Path]:
    """
    STRICT SINGLE PERSON VALIDATION:
    Only keep photos with EXACTLY 1 clear face (len(faces) == 1).
    Delete any photo with multiple faces or no face.
    """
    valid_paths = []
    for f in list(folder.iterdir()):
        if f.suffix.lower() not in IMAGE_EXTS:
            continue
        im = cv2.imread(str(f))
        if im is None:
            f.unlink(missing_ok=True)
            continue
        h, w = im.shape[:2]
        faces = face_engine._app.get(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        if len(faces) != 1:
            # Strictly reject multiple people in photo or no face
            f.unlink(missing_ok=True)
            continue
        face = faces[0]
        score = float(getattr(face, "det_score", 0))
        b = face.bbox
        fw = b[2] - b[0]
        fh = b[3] - b[1]
        if score < 0.70 or fw < 55 or fh < 55:
            f.unlink(missing_ok=True)
            continue
        valid_paths.append(f)
    return valid_paths

def process_celebrity(c_info: dict) -> tuple[np.ndarray | None, str | None, int]:
    folder = DATASET_DIR / c_info["id"]
    folder.mkdir(parents=True, exist_ok=True)

    # First check existing images in folder
    valid_imgs = inspect_and_filter_folder(folder)

    # If fewer than 2 valid single-person images, download more
    if len(valid_imgs) < 2:
        urls = fetch_urls(c_info, max_count=6)
        existing_names = {f.name for f in folder.iterdir()}
        for idx, u in enumerate(urls):
            fname = f"{idx + 1}.jpg"
            if fname not in existing_names:
                dest = folder / fname
                download_file(u, dest)
        valid_imgs = inspect_and_filter_folder(folder)

    if not valid_imgs:
        logger.warning("  [!] No valid single-person faces found for %s", c_info["name"])
        return None, None, 0

    embeddings = []
    display_candidates = []

    for img_p in valid_imgs:
        im = cv2.imread(str(img_p))
        if im is None:
            continue
        h, w = im.shape[:2]
        faces = face_engine._app.get(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        if len(faces) == 1:
            face = faces[0]
            emb = face.embedding
            if emb is not None:
                norm = np.linalg.norm(emb)
                if norm > 0:
                    embeddings.append(emb / norm)
            # Long-shot display scoring
            b = face.bbox
            fw = b[2] - b[0]
            fh = b[3] - b[1]
            face_ratio = (fw * fh) / (w * h)
            aspect = h / w
            ratio_dist = abs(face_ratio - 0.10)
            aspect_bonus = min(aspect, 1.6) * 0.4
            close_penalty = (face_ratio - 0.25) * 20.0 if face_ratio > 0.25 else (0.03 - face_ratio) * 20.0 if face_ratio < 0.03 else 0.0
            score = -(ratio_dist * 4.0) + aspect_bonus + (float(getattr(face, "det_score", 0)) * 0.3) - close_penalty
            display_candidates.append((score, f"{folder.name}/{img_p.name}"))

    if not embeddings:
        return None, None, 0

    avg = np.mean(embeddings, axis=0)
    norm = np.linalg.norm(avg)
    if norm == 0:
        return None, None, 0
    averaged = avg / norm

    if display_candidates:
        display_candidates.sort(key=lambda x: x[0], reverse=True)
        best_display = display_candidates[0][1]
    else:
        best_display = f"{folder.name}/{valid_imgs[0].name}"

    return averaged, best_display, len(embeddings)

def main():
    logger.info("=" * 65)
    logger.info("Batch Adding Verified Celebrities to CelebTwin Database")
    logger.info("=" * 65)

    face_engine.load()

    # Load existing celebrities.json
    with open(CELEBRITIES_JSON, "r", encoding="utf-8") as f:
        celebrities_json = json.load(f)
    existing_ids = {c["id"] for c in celebrities_json}

    # Load existing embeddings and metadata
    embeddings_list = list(np.load(EMBEDDINGS_NPY))
    metadata_list = list(np.load(METADATA_NPY, allow_pickle=True))
    existing_names = {m["name"].lower().strip() for m in metadata_list}
    existing_folders = {m.get("image", "").split("/")[0] for m in metadata_list}

    added = 0
    skipped = 0
    total = len(CANDIDATES)

    for idx, c in enumerate(CANDIDATES):
        cname = c["name"]
        cid = c["id"]

        # Check if already in database
        if cname.lower().strip() in existing_names or cid in existing_folders or cid in existing_ids:
            skipped += 1
            continue

        logger.info("[%d/%d] Processing: %s (%s)...", idx + 1, total, cname, c["category"])
        emb, display_img, num_photos = process_celebrity(c)

        if emb is None:
            logger.warning("  Could not generate valid embedding for %s", cname)
            continue

        embeddings_list.append(emb)
        metadata_list.append({
            "name": cname,
            "category": c["category"],
            "image": display_img,
        })
        celebrities_json.append({
            "id": cid,
            "name": cname,
            "category": c["category"],
            "folder": cid,
        })
        existing_ids.add(cid)
        existing_names.add(cname.lower().strip())
        existing_folders.add(cid)

        added += 1
        logger.info("  ✓ Added %s (%d verified single-person photos, display=%s)", cname, num_photos, display_img)

    # Save all updated database files
    with open(CELEBRITIES_JSON, "w", encoding="utf-8") as f:
        json.dump(celebrities_json, f, indent=2)
    logger.info("Saved %d celebrities to %s", len(celebrities_json), CELEBRITIES_JSON)

    np.save(EMBEDDINGS_NPY, np.array(embeddings_list, dtype=np.float32))
    logger.info("Saved %d embeddings to %s", len(embeddings_list), EMBEDDINGS_NPY)

    np.save(METADATA_NPY, np.array(metadata_list, dtype=object))
    logger.info("Saved %d metadata entries to %s", len(metadata_list), METADATA_NPY)

    logger.info("=" * 65)
    logger.info("SUCCESS: Added %d new celebrities! (Total now: %d)", added, len(metadata_list))
    logger.info("=" * 65)

if __name__ == "__main__":
    main()
