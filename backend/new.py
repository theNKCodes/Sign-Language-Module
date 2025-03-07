from gramformer import Gramformer
import torch

gf = Gramformer(models = 1, use_gpu=False) # 1=corrector, 2=detector
res = gf.correct("He go to school every day", max_candidates=1)
print(res)

