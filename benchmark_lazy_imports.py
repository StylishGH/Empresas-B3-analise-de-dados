import time
import sys
import subprocess

TEST_MODULES = [
    "pandas",
    "numpy",
    "plotly.express",
    "plotly.graph_objects",
    "yfinance",
    "sklearn.ensemble",
    "sklearn.preprocessing",
    "streamlit",
]

print("=" * 65)
print(f"🐍 PYTHON 3.15.0 - BENCHMARK DE LAZY IMPORTS (PEP 690)")
print(f"Executável: {sys.executable}")
print("=" * 65)

# 1. Teste de Import Eager (Padrão Tradicional)
code_eager = """
import time
t0 = time.perf_counter()
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import streamlit as st
t1 = time.perf_counter()
print(f"EAGER_TOTAL_MS:{(t1 - t0)*1000:.2f}")
"""

# 2. Teste de Explicit Lazy Import (Sintaxe 'lazy import' e 'lazy from')
code_lazy_syntax = """
import time, sys
t0 = time.perf_counter()
lazy import pandas as pd
lazy import numpy as np
lazy import plotly.express as px
lazy import plotly.graph_objects as go
lazy import yfinance as yf
lazy from sklearn.ensemble import RandomForestClassifier
lazy from sklearn.preprocessing import StandardScaler
lazy import streamlit as st
t1 = time.perf_counter()

# Verifica quantos módulos foram de fato carregados
loaded_before = [m for m in ['pandas', 'numpy', 'plotly', 'yfinance', 'sklearn', 'streamlit'] if m in sys.modules]

# Agora aciona apenas o numpy e pandas
t2 = time.perf_counter()
arr = np.array([1, 2, 3])
df = pd.DataFrame({'x': arr})
t3 = time.perf_counter()

loaded_after = [m for m in ['pandas', 'numpy', 'plotly', 'yfinance', 'sklearn', 'streamlit'] if m in sys.modules]

print(f"LAZY_SYNTAX_IMPORT_MS:{(t1 - t0)*1000:.3f}")
print(f"LOADED_BEFORE_ACCESS:{loaded_before}")
print(f"FIRST_ACCESS_NP_PD_MS:{(t3 - t2)*1000:.2f}")
print(f"LOADED_AFTER_ACCESS:{loaded_after}")
"""

# 3. Teste com flag global -X lazy_imports=all
code_global_flag = """
import time, sys
t0 = time.perf_counter()
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import streamlit as st
t1 = time.perf_counter()

loaded = [m for m in ['pandas', 'numpy', 'plotly', 'yfinance', 'sklearn', 'streamlit'] if m in sys.modules]
print(f"GLOBAL_FLAG_IMPORT_MS:{(t1 - t0)*1000:.3f}")
print(f"GLOBAL_LOADED:{loaded}")
"""

print("\n[1/3] Medindo Import Tradicional (Eager)...")
p1 = subprocess.run([sys.executable, "-c", code_eager], capture_output=True, text=True)
print(p1.stdout.strip())

print("\n[2/3] Medindo Sintaxe Nativa Python 3.15 ('lazy import' / 'lazy from')...")
p2 = subprocess.run([sys.executable, "-c", code_lazy_syntax], capture_output=True, text=True)
print(p2.stdout.strip())

print("\n[3/3] Medindo Flag Global (-X lazy_imports=all)...")
p3 = subprocess.run([sys.executable, "-X", "lazy_imports=all", "-c", code_global_flag], capture_output=True, text=True)
print(p3.stdout.strip())

print("\n" + "=" * 65)
