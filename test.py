import pprint
import json
import re

j = "[{\"alternatives\": [{\"transcript\": \"servired Buenos d\\u00edas la tiene Marcela Cano con quien tengo el gusto Se\\u00f1orita me compartes tu n\\u00famero de empleado por favor Dios quien su santo desierto Gracias Ahora me indica el n\\u00famero de folio que vamos a revisar por favor l de Laura 1605 33489 489 gracias\", \"confidence\": 0.95684695}]}, {\"alternatives\": [{\"transcript\": \"corredores se\\u00f1orita est\\u00e1 en este folio se report\\u00f3 que no se pudo no pod\\u00edan ser Ingresar a tarjeta sube en su acto cuento bien Todav\\u00eda no ha tenido respuesta de la 18 es que me coment\\u00f3 me lleg\\u00f3 me lleg\\u00f3 me dice solicitud de visto bueno no malo 2 para cierre de registro pero intenta ingresar pero no me no me da opci\\u00f3n\", \"confidence\": 0.8870713}]}, {\"alternatives\": [{\"transcript\": \"hojas me sigues marcando el error ayer de hecho que me lleg\\u00f3 la primera lo de negri y ahorita me est\\u00e1 llegando la otra pero no lo voy a poder denegar porque no estoy en la oficina\", \"confidence\": 0.8981022}]}, {\"alternatives\": [{\"transcript\": \"yo cuando voy que sepas que no apoyan a se\\u00f1orita sigo en l\\u00ednea gracias yo con vos\", \"confidence\": 0.7552649}]}, {\"alternatives\": [{\"transcript\": \"en ese tiempo en espera se\\u00f1orita los siguientes es necesario que vuelva a solicitar la alta del aplicativo Aproximadamente cu\\u00e1nto tiempo hace que ingreso se\\u00f1orita No pues el jueves antes del d\\u00eda jueves\", \"confidence\": 0.9079067}]}, {\"alternatives\": [{\"transcript\": \"es que ya no tiene raz\\u00f3n al tel aplicativo beso tutorial Esto me pasa cada Como cada mes porque me sali\\u00f3 la \\u00faltima vez que me pas\\u00f3 fue el m\\u00e1s loco que c\\u00f3mo and\\u00e1s pasado m\\u00e1s o menos y me pidieron que ya nada yo un formato en donde me tengo que pedir la alta o algo as\\u00ed me lo firmaba Fernando por internet todav\\u00eda\", \"confidence\": 0.898167}]}, {\"alternatives\": [{\"transcript\": \"osea no es la primera vez que me pasa No s\\u00e9 si me pasas s\\u00faper seguido como mes y medio m\\u00e1s o menos\", \"confidence\": 0.8298816}]}, {\"alternatives\": [{\"transcript\": \"y le coment\\u00f3 la \\u00faltima vez que llen\\u00f3 un formato y se firm\\u00f3 por m\\u00ed por mi zona y se mand\\u00f3 tu t\\u00eda interventor\\u00eda\", \"confidence\": 0.72492164}]}, {\"alternatives\": [{\"transcript\": \"entonces hace aproximadamente menos de 8 d\\u00edas que fue la \\u00faltima vez que ingreso de manera incorrecta\", \"confidence\": 0.88769865}]}, {\"alternatives\": [{\"transcript\": \"bien Perm\\u00edteme para realizar el tema gracias\", \"confidence\": 0.8999392}]}, {\"alternatives\": [{\"transcript\": \"agradezco su tiempo en espera se\\u00f1orita P\\u00e9rez\", \"confidence\": 0.90504724}]}, {\"alternatives\": [{\"transcript\": \"agradezco su tiempo en espera se\\u00f1orita P\\u00e9rez\", \"confidence\": 0.9420534}]}, {\"alternatives\": [{\"transcript\": \"agradezco su tiempo en espera se\\u00f1orita P\\u00e9rez\", \"confidence\": 0.9617364}]}, {\"alternatives\": [{\"transcript\": \"continuar l\\u00ednea se\\u00f1orita continuar l\\u00ednea se\\u00f1orita\", \"confidence\": 0.727758}]}]"
# j = re.sub(r"{\s*(\w)", r'{"\1', j)
# j = re.sub(r",\s*(\w)", r',"\1', j)
# j = re.sub(r"(\w):", r'\1":', j)
# pprint.pprint(resultado)
rr = json.loads(j)
# print(type(rr))

# for r in rr:
#     print(r['alternatives'][0]['transcript']);
# print(resultado)
# rr = json.loads(resultado)
# pprint.pprint(rr)
text = ""
sentences = []
confidence = []
for r in rr:
    print(r['alternatives'][0]['transcript'])
    text = text + r['alternatives'][0]['transcript'] + ". "
    confidence.append(float(r['alternatives'][0]['confidence']))
    sentences.append(r['alternatives'][0]['transcript'])

# print(text)
# print(confidence)
# print(len(confidence))
# print(sum(confidence)/len(confidence))

for idx,sentence in enumerate(sentences):
    print(sentence," => ",confidence[idx])
