import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

def generate_sales_dataset(num_rows=1000):
    """Generate a realistic sales/e-commerce dataset with 20+ attributes"""

    # Date range: last 2 years
    start_date = datetime.now() - timedelta(days=730)
    dates = [start_date + timedelta(days=random.randint(0, 730)) for _ in range(num_rows)]

    # Core dimensions
    regions = ['North', 'South', 'East', 'West', 'Central']
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys', 'Food']
    subcategories = {
        'Electronics': ['Phones', 'Laptops', 'Cameras', 'Audio', 'Accessories'],
        'Clothing': ['Men', 'Women', 'Kids', 'Shoes', 'Bags'],
        'Home & Garden': ['Furniture', 'Kitchen', 'Decor', 'Tools', 'Outdoor'],
        'Sports': ['Fitness', 'Team Sports', 'Outdoor', 'Apparel', 'Equipment'],
        'Books': ['Fiction', 'Non-Fiction', 'Academic', 'Children', 'Comics'],
        'Toys': ['Educational', 'Action Figures', 'Board Games', 'Dolls', 'Puzzles'],
        'Food': ['Snacks', 'Beverages', 'Organic', 'Frozen', 'Gourmet']
    }

    channels = ['Online', 'Retail Store', 'Mobile App', 'Phone', 'Partner']
    customer_segments = ['New', 'Returning', 'VIP', 'Wholesale', 'Corporate']
    payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'UPI', 'Cash', 'Net Banking']
    shipping_methods = ['Standard', 'Express', 'Overnight', 'Same Day', 'Pickup']

    data = []

    for i in range(num_rows):
        order_date = dates[i]
        category = random.choice(categories)
        subcategory = random.choice(subcategories[category])
        region = random.choice(regions)
        channel = np.random.choice(channels, p=[0.45, 0.25, 0.15, 0.05, 0.10])
        segment = np.random.choice(customer_segments, p=[0.3, 0.4, 0.1, 0.1, 0.1])

        # Realistic relationships between attributes
        base_price = {
            'Electronics': 500, 'Clothing': 60, 'Home & Garden': 120,
            'Sports': 80, 'Books': 25, 'Toys': 35, 'Food': 15
        }[category]

        quantity = np.random.choice([1, 2, 3, 4, 5], p=[0.6, 0.2, 0.1, 0.07, 0.03])
        unit_price = round(base_price * random.uniform(0.5, 2.5), 2)
        discount_pct = np.random.choice([0, 5, 10, 15, 20, 30], p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05])

        gross_amount = round(unit_price * quantity, 2)
        discount_amount = round(gross_amount * discount_pct / 100, 2)
        tax_amount = round((gross_amount - discount_amount) * 0.18, 2) # 18% GST
        net_amount = round(gross_amount - discount_amount + tax_amount, 2)

        cost_price = round(unit_price * random.uniform(0.4, 0.7), 2)
        profit = round((unit_price - cost_price) * quantity - discount_amount, 2)
        profit_margin = round(profit / gross_amount * 100, 2) if gross_amount > 0 else 0

        # Time-based features
        ship_date = order_date + timedelta(days=random.randint(1, 7))
        delivery_date = ship_date + timedelta(days=random.randint(1, 10))
        is_weekend = order_date.weekday() >= 5
        is_holiday = random.random() < 0.05

        # Customer features
        customer_id = f"CUST{random.randint(10000, 99999)}"
        customer_age = max(18, int(np.random.normal(38, 12)))
        customer_rating = round(random.uniform(1, 5), 1)
        days_since_last_order = random.randint(0, 365) if segment!= 'New' else 0

        # Operational metrics
        shipping_cost = round(random.uniform(0, 50) if gross_amount < 500 else 0, 2)
        return_flag = random.random() < 0.08
        return_reason = random.choice(['Defective', 'Wrong Item', 'Not Needed', 'Late Delivery', None]) if return_flag else None
        customer_satisfaction = random.randint(1, 5) if not return_flag else random.randint(1, 3)

        # Marketing attributes
        campaign = random.choice(['Summer Sale', 'Black Friday', 'New Year', 'Clearance', 'None'])
        ad_spend = round(random.uniform(0, 50) if campaign!= 'None' else 0, 2)
        clicks = random.randint(0, 20) if campaign!= 'None' else 0

        row = {
            'Order_ID': f'ORD{i+100000}',
            'Order_Date': order_date.strftime('%Y-%m-%d'),
            'Ship_Date': ship_date.strftime('%Y-%m-%d'),
            'Delivery_Date': delivery_date.strftime('%Y-%m-%d'),
            'Order_Month': order_date.strftime('%Y-%m'),
            'Order_Quarter': f'Q{(order_date.month-1)//3 + 1} {order_date.year}',
            'Order_Year': order_date.year,
            'Is_Weekend': is_weekend,
            'Is_Holiday': is_holiday,

            'Customer_ID': customer_id,
            'Customer_Name': fake.name(),
            'Customer_Age': customer_age,
            'Customer_Gender': random.choice(['Male', 'Female', 'Other']),
            'Customer_Segment': segment,
            'Customer_City': fake.city(),
            'Customer_State': fake.state(),
            'Customer_Region': region,
            'Customer_Rating': customer_rating,
            'Days_Since_Last_Order': days_since_last_order,

            'Product_Category': category,
            'Product_Subcategory': subcategory,
            'Product_Name': fake.catch_phrase(),
            'Product_SKU': fake.bothify(text='SKU-####-????').upper(),
            'Supplier': fake.company(),

            'Sales_Channel': channel,
            'Payment_Method': payment_methods[np.random.choice(len(payment_methods), p=[0.35,0.2,0.15,0.15,0.05,0.1])],
            'Shipping_Method': shipping_methods[np.random.choice(len(shipping_methods), p=[0.5,0.3,0.1,0.05,0.05])],

            'Quantity': quantity,
            'Unit_Price': unit_price,
            'Unit_Cost': cost_price,
            'Gross_Sales': gross_amount,
            'Discount_Percent': discount_pct,
            'Discount_Amount': discount_amount,
            'Tax_Amount': tax_amount,
            'Shipping_Cost': shipping_cost,
            'Net_Sales': net_amount,
            'Profit': profit,
            'Profit_Margin_Percent': profit_margin,

            'Marketing_Campaign': campaign,
            'Ad_Spend': ad_spend,
            'Ad_Clicks': clicks,

            'Returned': return_flag,
            'Return_Reason': return_reason,
            'Customer_Satisfaction': customer_satisfaction,
            'Delivery_Days': (delivery_date - order_date).days,
            'Review_Score': random.randint(1, 5)
        }
        data.append(row)

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    print("Generating 1000 row dataset...")
    df = generate_sales_dataset(1000)

    # Save to CSV
    filename = "sales_dataset_1000_rows.csv"
    df.to_csv(filename, index=False)

    print(f"✅ Generated {filename}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {len(df.columns)}")
    print("\nColumn types:")
    print(df.dtypes.value_counts())
    print("\nFirst 3 rows:")
    print(df.head(3))
    print(f"\nMemory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")