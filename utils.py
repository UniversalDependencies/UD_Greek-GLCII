import os
import conllu

def build_fp(rg, split): # rg= "org"|"trg"
  return "../sv_swell-{}-ud-{}.conllu".format(rg, split)

def parse_file(fp):
  if not os.path.exists(fp):
    print("{} does not exist!".format(fp))
    exit(-1)
  with open(fp) as h:
    txt = h.read()
  return [sent for sent in conllu.parse(txt)]

def assign_seq_id(rg, split, s, n):
  s.metadata["sent_id"] = "{}-{}-{}".format(rg, n, split)

def reconstruct_text(s):
  forms = [t["form"] for t in s]
  s.metadata["text"] = " ".join(forms)