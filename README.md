# YOKATLAS MCP: Türk Yükseköğretim Atlası için MCP Sunucusu

Bu proje, [YÖKATLAS](https://yokatlas.yok.gov.tr/) verilerine erişimi kolaylaştıran bir [FastMCP](https://gofastmcp.com/) sunucusu oluşturur. Bu sayede, YÖKATLAS'tan lisans ve önlisans program arama ve detaylı istatistik getirme işlemleri, Model Context Protocol (MCP) destekleyen LLM (Büyük Dil Modeli) uygulamaları (örneğin Claude Desktop veya [5ire](https://5ire.app)) ve diğer istemciler tarafından araç (tool) olarak kullanılabilir hale gelir.

![YOKATLAS MCP Örneği](./ornek.png)

🎯 **Temel Özellikler**

* YÖKATLAS tercih kılavuzu JSON API'sine programatik erişim için standart bir MCP arayüzü.
* Aşağıdaki yetenekler:
    * **Birleşik Akıllı Arama:** Lisans + önlisans tek arama; fuzzy matching ile üniversite/program/il adı çözümlemesi (örn: "boğaziçi" → "BOĞAZİÇİ ÜNİVERSİTESİ")
    * **4 Yıllık İstatistik:** Her programa ait kontenjan, yerleşen, taban puanı, başarı sırası, akademik kadro ve KPSS verileri tek seferde (current + 3 history)
    * **Lookup Araçları:** Üniversite, program grubu ve il listelerine doğrudan erişim
    * **Filtreleme:** Puan türü (SAY/SÖZ/EA/DİL/TYT), üniversite türü (DEVLET/VAKIF), başarı sırası aralığı, sayfalama ve sıralama
* Claude Desktop uygulaması ile `fastmcp install` komutu (veya manuel yapılandırma) kullanılarak kolay entegrasyon.
* YOKATLAS MCP [5ire](https://5ire.app) gibi Claude Desktop haricindeki MCP istemcilerini de destekler.

> ⚠️ **v0.6.0 Breaking Change** — YÖK Atlas Nisan 2026'da React tabanlı SPA'ya geçti, eski HTML scraping endpoint'leri ve detaylı atlas verileri (cinsiyet/lise alanı dağılımı, akademisyen ünvan dağılımı, KPSS yıllara göre, vb.) site genelinden kaldırıldı. Bu MCP yeni JSON API'ye karşı yazıldı; sadece resmî API'nin sunduğu temel istatistikler döner.

---

## 🚀 5 Dakikada Başla (Remote MCP)

### ✅ Kurulum Gerektirmez! Hemen Kullan!

🔗 **Remote MCP Adresi:** `https://yokatlasmcp.fastmcp.app/mcp`

### Claude Desktop ile Kullanım

1. **Claude Desktop'ı açın**
2. **Settings → Connectors → Add Custom Connector**
3. **Bilgileri girin:**
   - **Name:** `YOKATLAS MCP`
   - **URL:** `https://yokatlasmcp.fastmcp.app/mcp`
4. **Add** butonuna tıklayın
5. **Hemen kullanmaya başlayın!** 🎉

### Google Antigravity ile Kullanım

1. **Agent session** açın ve editörün yan panelindeki **"…"** dropdown menüsüne tıklayın
2. **MCP Servers** seçeneğini seçin - MCP Store açılacak
3. Üstteki **Manage MCP Servers** butonuna tıklayın
4. **View raw config** seçeneğine tıklayın
5. `mcp_config.json` dosyasına aşağıdaki yapılandırmayı ekleyin:

```json
{
  "mcpServers": {
    "yokatlas-mcp": {
      "serverUrl": "https://yokatlasmcp.fastmcp.app/mcp/",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }
}
```

> 💡 **İpucu:** Remote MCP sayesinde Python, uv veya herhangi bir kurulum yapmadan doğrudan Claude Desktop üzerinden YÖKATLAS verilerine erişebilirsiniz!

---

## 🚀 Claude Haricindeki Modellerle Kullanmak İçin Çok Kolay Kurulum (Örnek: 5ire için)

Bu bölüm, YOKATLAS MCP aracını 5ire gibi Claude Desktop dışındaki MCP istemcileriyle kullanmak isteyenler içindir.

* **Python Kurulumu:** Sisteminizde Python 3.12 kurulu olmalıdır. Kurulum sırasında "**Add Python to PATH**" (Python'ı PATH'e ekle) seçeneğini işaretlemeyi unutmayın. [Buradan](https://www.python.org/downloads/) indirebilirsiniz.
* **Git Kurulumu (Windows):** Bilgisayarınıza [git](https://git-scm.com/downloads/win) yazılımını indirip kurun. "Git for Windows/x64 Setup" seçeneğini indirmelisiniz.
* **`uv` Kurulumu:**
    * **Windows Kullanıcıları (PowerShell):** Bir CMD ekranı açın ve bu kodu çalıştırın: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
    * **Mac/Linux Kullanıcıları (Terminal):** Bir Terminal ekranı açın ve bu kodu çalıştırın: `curl -LsSf https://astral.sh/uv/install.sh | sh`
* **Microsoft Visual C++ Redistributable (Windows):** Bazı Python paketlerinin doğru çalışması için gereklidir. [Buradan](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) indirip kurun.
* İşletim sisteminize uygun [5ire](https://5ire.app) MCP istemcisini indirip kurun.
* 5ire'ı açın. **Workspace -> Providers** menüsünden kullanmak istediğiniz LLM servisinin API anahtarını girin.
* **Tools** menüsüne girin. **+Local** veya **New** yazan butona basın.
    * **Tool Key:** `yokatlasmcp`
    * **Name:** `YOKATLAS MCP`
    * **Command:**
        ```
        uvx --from git+https://github.com/saidsurucu/yokatlas-mcp yokatlas-mcp
        ```
    * **Save** butonuna basarak kaydedin.

* Şimdi **Tools** altında **YOKATLAS MCP**'yi görüyor olmalısınız. Üstüne geldiğinizde sağda çıkan butona tıklayıp etkinleştirin (yeşil ışık yanmalı).
* Artık YOKATLAS MCP ile konuşabilirsiniz.

---

## ⚙️ Claude Desktop Manuel Kurulumu

1.  **Ön Gereksinimler:** Python, `uv`, (Windows için) Microsoft Visual C++ Redistributable'ın sisteminizde kurulu olduğundan emin olun. Detaylı bilgi için yukarıdaki "5ire için Kurulum" bölümündeki ilgili adımlara bakabilirsiniz.
2.  Claude Desktop **Settings -> Developer -> Edit Config**.
3.  Açılan `claude_desktop_config.json` dosyasına `mcpServers` altına ekleyin:

    ```json
    {
      "mcpServers": {
        "YOKATLAS MCP": {
          "command": "uvx",
          "args": [
            "--from", "git+https://github.com/saidsurucu/yokatlas-mcp",
            "yokatlas-mcp"
          ]
        }
      }
    }
    ```

4.  Claude Desktop'ı kapatıp yeniden başlatın.

---

## 🛠️ Kullanılabilir Araçlar (MCP Tools)

Bu FastMCP sunucusu LLM modelleri için aşağıdaki araçları sunar:

### 🔍 Arama

* **`search_programs`**: Lisans + önlisans birleşik arama (akıllı fuzzy matching).
    * **Parametreler:**
        * `degree_type`: `'bachelor'` (lisans) veya `'associate'` (önlisans). Boş bırakılırsa ikisi de döner.
        * `puan_turu`: `SAY`, `SÖZ`/`SOZ`, `EA`, `DİL`/`DIL`, `TYT` (ASCII varyantlar otomatik normalize edilir).
        * `universite`, `program`, `il`: Smart fuzzy match (örn. `"boğaziçi"`, `"bilgisayar"`, `"ankara"`).
        * `universite_turu`: `DEVLET` veya `VAKIF`.
        * `kilavuz_kodu`: `int` — tek programa filtre (eski "atlas detayı" use-case'i için).
        * `min_basari_sirasi`, `max_basari_sirasi`: Başarı sırası aralığı.
        * `page`, `size`, `sort_by`, `direction`: Sayfalama ve sıralama (default: `basariSirasi ASC`, `size=20`, max `size=500`).
    * **Döndürülen Veri:** Her sonuç 4 yıllık istatistikleri (`current` + `history`) içerir: kontenjan, yerleşen, taban puanı, başarı sırası, KPSS skorları, akademik kadro sayıları.

### 📚 Lookup Araçları

* **`list_universities`**: YÖKATLAS'taki tüm üniversiteleri (`universite_id`, `universite_adi`) listeler.
* **`list_program_groups`**: Tüm program gruplarını (`birim_grup_id`, `birim_grup_adi`, `puan_turu`) listeler — geçerli `program` filtre değerlerini keşfetmek için kullanın.
* **`list_cities`**: 81 ili (`il_kodu`, `il_adi`) listeler.

### 🔄 v0.5 → v0.6 Migration

Eski API'den geçenler için kısaca:

| Eski (v0.5) | Yeni (v0.6) |
|---|---|
| `search_bachelor_degree_programs` | `search_programs(degree_type='bachelor', ...)` |
| `search_associate_degree_programs` | `search_programs(degree_type='associate', ...)` |
| `get_bachelor_degree_atlas_details(yop_kodu, year)` | `search_programs(kilavuz_kodu=N)` (4 yıllık veri search içinde) |
| `get_associate_degree_atlas_details(yop_kodu, year)` | `search_programs(kilavuz_kodu=N)` |
| `score_type` | `puan_turu` (TYT eklendi) |
| `fee_type` / `education_type` / `availability` | Kaldırıldı (yeni API'de doğrudan karşılığı yok) |
| `yop_kodu` (str) | `kilavuz_kodu` (int) |

---

## 📜 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakınız.
