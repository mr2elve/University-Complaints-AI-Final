import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from src.model_loader import load_model
from src.inference import predict_batch

bundle=load_model()
results=predict_batch(bundle,[
    'Сабақ кестесі дұрыс жасалмаған. Екі пән бір уақытта тұр.',
    'Жатақханада бірнеше күннен бері ыстық су жоқ. Студенттер қатты қиналып жатыр.',
    'Оқу ақысын төледім, бірақ жүйеде төлем көрсетілмейді. Осы мәселені шешуге көмектесіңіздер.',
])
print(json.dumps(results,ensure_ascii=False,indent=2))
print('PASS: strict CPU checkpoint load and real inference on three Kazakh complaints.')
