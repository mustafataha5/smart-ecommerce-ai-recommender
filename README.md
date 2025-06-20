# Smart E-Commerce AI Recommender

An AI-driven recommendation system for e-commerce platforms. This project integrates multiple machine learning models and techniques to deliver smart product suggestions, user insights, and sales forecasting, all exposed via a Flask API.

---

## 📁 Project Structure

| Folder | Description |
|--------|-------------|
| `01 Data analysis (user by country)` | Visual insights on user distribution across countries |
| `02 Data analysis (users info)` | Exploration of user attributes (age, gender, etc.) |
| `03 Data analysis (product info)` | Analysis of product types, sales, and popularity |
| `04 Association` | Association rules to find product co-purchases |
| `05 Classification` | Predict recommended products based on user features |
| `06 Time Series` | Forecasting future sales using historical data |
| `server/` | Flask app to serve predictions via REST API |

---

## 💡 Features

- ✅ **Association Rules**: Products that are often bought together (Apriori / FP-Growth).
- ✅ **Classification**: Personalized product recommendations based on user age, gender, and country.
- ✅ **Time Series Forecasting**: Predicts future sales using statistical and ML methods.
- ✅ **REST API**: Built with Flask to serve models for external use.

---

## 🛠 Tech Stack

- Python: `pandas`, `scikit-learn`, `statsmodels`, `mlxtend`
- Flask for serving APIs
- Jupyter Notebooks for experimentation
- Matplotlib / Seaborn for data visualization

---

## 🚀 Getting Started

```bash
git clone https://github.com/mustafataha5/smart-ecommerce-ai-recommender.git
cd smart-ecommerce-ai-recommender
pip install -r requirements.txt
cd server
python app.py
