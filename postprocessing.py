import argparse
import os.path
import shutil
import conllu
from utils import *

MANDATORY_META = ["sent_id", "text"]
SHAREABLE_SWELL_META = ["l1", "writing_language", "approximate_level"]

def remove_xpos(t):
  t["xpos"] = "_"

def sort_feats(t):
  if t["feats"]:
    t["feats"] = dict(sorted(t["feats"].items(), key=lambda kv: kv[0].lower()))

def fix_goeswith(t,s):
  if t["deprel"] == "goeswith":
    head_index = t["head"] - 1 # probably would not quite work with MWTs
    if not s[head_index]["feats"]:
      s[head_index]["feats"] = {}
    s[head_index]["feats"]["Typo"] = "Yes"

def add_typos(t):
  if t["deprel"] != "goeswith":
    if t["misc"]:
      if "CorrectionLabels" in t["misc"]:
        labels = t["misc"]["CorrectionLabels"]
        if any([label.startswith("O") for label in labels.split(";")]):
          if not t["feats"]:
            t["feats"] = {}
          t["feats"]["Typo"] = "Yes"

def fix_adv_lemmas(t):
  upos = t["upos"]
  form = t["form"]
  lemma = t["lemma"]
  if upos == "ADV" and form.endswith("t") and not lemma.endswith("t"):
    auto_lemma = form
    print("form: {}\nlemma: {}\n\nreplacing lemma with {}".format(
      form, lemma, auto_lemma))
    user_lemma = input(
      "enter to confirm, x + enter to skip, new lemma + enter to overwrite: ")
    if user_lemma != "x":
      t["lemma"] = user_lemma if user_lemma else auto_lemma

def filter_meta(s, whitelist=MANDATORY_META):
  for key in list(s.metadata):
    if not key in whitelist:
      s.metadata.pop(key)

def rm_unmarked(t):
  split_deprel = t["deprel"].split(":")
  if len(split_deprel) > 1 and split_deprel[1] == "unmarked":
    t["deprel"] = t["deprel"].replace(":unmarked", "")

def fix_stars(t):
  if t["deprel"].split(":")[-1] == "*":
    if not t["misc"]:
      t["misc"] = {}
    t["misc"]["IntendedDeprel"] = t["deprel"].replace(":*", "")
    t["deprel"] = "dep"

def fix_ns_auxs(t):
  if t["upos"] == "AUX":
    if not t["misc"]:
      t["misc"] = {}
    if t["lemma"] in ["εχω", "ΕΧΩ"]:
      t["misc"]["IntendedLemma"] = t["lemma"]
      t["lemma"] = "έχω"
    if t["lemma"] in ["ειμαι", "ΕΙΝΑΙ", "ΕΙΜΑΙ", "εἰμαι", "ιμαι", "είμαη"]:
      t["misc"]["IntendedLemma"] = t["lemma"]
      t["lemma"] = "είμαι"
    if t["lemma"] in ["ΝΑ"]:
      t["misc"]["IntendedLemma"] = t["lemma"]
      t["lemma"] = "να"
  
def fix_uppercase_lemmas(t):
  if t["lemma"].isupper():
    if t["upos"] == "PROPN":
      t["lemma"] = t["lemma"].title()
    else:
      t["lemma"] = t["lemma"].lower()

def add_missing_arts(t):
  if t["lemma"] == "ο" and t["upos"] == "DET":
    if not t["feats"]:
      t["feats"] = {}
    t["feats"]["PronType"] = "Art"

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Automatic postprocessing for UD_Greek-GLCII")
  parser.add_argument("split", help="train|dev|test")
  parser.add_argument(
    "--assign_seq_ids", 
    help="reassign (sequential) IDs",
    action="store_true")
  parser.add_argument(
    "--remove_xpos", 
    help="remove XPOS tags",
    action="store_true")
  parser.add_argument(
    "--sort_feats", 
    help="sort morphological features alphabetically",
    action="store_true")
  parser.add_argument(
    "--fix_goeswith", 
    help="add Typo=Yes to all heads of goeswith relations",
    action="store_true")  
  parser.add_argument(
    "--add_typos", 
    help="add Typo=Yes to original tokens labelled O*",
    action="store_true") 
  parser.add_argument(
    "--reconstruct_text", 
    help="reconstruct linear text and store it as metadata",
    action="store_true")
  parser.add_argument(
    "--fix_adv_lemmas", 
    help="fix lemmas of ADVs in -t derived from adjectives (interactive)",
    action="store_true")
  parser.add_argument(
    "--release",
    help="copy split to the given (UD) repo path, following the offical directory structure and naming conventions",
    default=None
  )
  parser.add_argument(
    "--filter_meta",
    help="remove overly sensitive and internal metadata (release only)",
    action="store_true"
  )
  parser.add_argument(
    "--rm_unmarked",
    help="get rid of the :unmarked subtype (release 2.17 only)",
    action="store_true"
  )
  parser.add_argument(
    "--fix_stars",
    help="fix deliberate violations, marked with :* (release 2.17 only)",
    action="store_true"
  )
  parser.add_argument(
    "--fix_ns_auxs",
    help="fix noncanonical auxiliary lemmas",
    action="store_true"
  )
  parser.add_argument(
    "--fix_uppercase_lemmas",
    help="lowercase all caps lemmas, excepts if PROPN",
    action="store_true"
  )
  parser.add_argument(
    "--add_missing_arts",
    help="add PronType=Art where missing",
    action="store_true"
  )

  args = parser.parse_args()
  
  org_fp = "el_glcii-ud-test.conllu"
  trg_fp = "not-to-release/el_glcii-ud-test-ref.conllu"

  pairs = list(zip(parse_file(org_fp), parse_file(trg_fp)))

  for (i,(org,trg)) in enumerate(pairs):
    if args.assign_seq_ids:
      assign_seq_id("org", args.split, org, i+1) 
      assign_seq_id("trg", args.split, trg, i+1)
    if args.reconstruct_text:
      reconstruct_text(org)
      reconstruct_text(trg)

    for token in org:
      if args.remove_xpos:
        remove_xpos(token)
      if args.fix_goeswith:
        fix_goeswith(token,org)
      if args.add_typos:
        add_typos(token)
      if args.fix_adv_lemmas:
        fix_adv_lemmas(token)
      if args.sort_feats:
        sort_feats(token)
      if args.fix_ns_auxs:
        fix_ns_auxs(token)
      if args.fix_uppercase_lemmas:
        fix_uppercase_lemmas(token)
      if args.add_missing_arts:
        add_missing_arts(token)

    for token in trg:
      if args.remove_xpos:
        remove_xpos(token)
      if args.fix_goeswith:
        fix_goeswith(token,trg)
      if args.fix_adv_lemmas:
        fix_adv_lemmas(token)
      if args.sort_feats:
        sort_feats(token)
      if args.fix_uppercase_lemmas:
        fix_uppercase_lemmas(token)
      if args.add_missing_arts:
        add_missing_arts(token)

  with open(org_fp, 'w') as org_h, open(trg_fp, 'w') as trg_h:
    for (org,trg) in pairs:
      org_h.writelines(org.serialize())
      trg_h.writelines(trg.serialize())
  
  if args.release:
    for (i,(org,trg)) in enumerate(pairs):
      if args.filter_meta:
        whitelist = MANDATORY_META + SHAREABLE_SWELL_META
        filter_meta(org, whitelist)
        filter_meta(trg, whitelist)

      for token in org:
        if args.rm_unmarked:
          rm_unmarked(token)
        if args.fix_stars:
          fix_stars(token)

      for token in trg:
        if args.rm_unmarked:
          rm_unmarked(token)

    org_release_fp = os.path.join(
      args.release, 
      "sv_swell-ud-{}.conllu".format(args.split))
    trg_release_fp = os.path.join(
        args.release,
        "not-to-release", 
        "sv_swell-ud-{}-trg.conllu".format(args.split))

    with open(org_release_fp, 'w') as org_h, open(trg_release_fp, 'w') as trg_h:
      for (org,trg) in pairs:
        org_h.writelines(org.serialize())
        trg_h.writelines(trg.serialize())

