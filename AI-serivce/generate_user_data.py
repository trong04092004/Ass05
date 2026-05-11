"""
Generate user_data.csv with 10000 samples for behavior tracking.
"""
import csv
import random
from datetime import datetime, timedelta

# Configuration
NUM_SAMPLES = 10000
NUM_USERS = 500
NUM_PRODUCTS = 200
SEED = 42

# Set seed for reproducibility
random.seed(SEED)

ACTIONS = ['view', 'add_to_cart', 'purchase', 'search_click', 'remove_from_cart', 'add_to_wishlist', 'rate_review', 'share']
CONTEXTS = ['home_page', 'product_detail', 'cart', 'checkout', 'search_results', 'category_page', 'profile', 'recommendation']

# Generate user IDs and product IDs
user_ids = list(range(1, NUM_USERS + 1))
product_ids = list(range(1, NUM_PRODUCTS + 1))

# Action weights (view is most common, purchase is less common)
action_weights = {
    'view': 40,
    'add_to_cart': 15,
    'purchase': 5,
    'search_click': 10,
    'remove_from_cart': 5,
    'add_to_wishlist': 8,
    'rate_review': 3,
    'share': 2,
}

def weighted_choice(actions, weights):
    """Choose action based on weights."""
    return random.choices(actions, weights=weights.values(), k=1)[0]

def generate_timestamp(base_time, offset_seconds):
    """Generate timestamp."""
    return (base_time + timedelta(seconds=offset_seconds)).strftime('%Y-%m-%d %H:%M:%S')

def generate_context(action):
    """Generate context based on action."""
    context_map = {
        'view': ['product_detail', 'home_page', 'search_results', 'category_page'],
        'add_to_cart': ['product_detail', 'cart', 'home_page'],
        'purchase': ['cart', 'checkout'],
        'search_click': ['search_results'],
        'remove_from_cart': ['cart'],
        'add_to_wishlist': ['product_detail', 'home_page'],
        'rate_review': ['product_detail'],
        'share': ['product_detail', 'home_page'],
    }
    return random.choice(context_map.get(action, CONTEXTS))

# User behavior patterns for more realistic sequences
BEHAVIOR_PATTERNS = [
    # Pattern 1: View -> Add to cart -> Purchase
    ['view', 'add_to_cart', 'purchase'],
    # Pattern 2: Search -> View -> Add to wishlist
    ['search_click', 'view', 'add_to_wishlist'],
    # Pattern 3: View -> Add to cart -> Remove -> Add again -> Purchase
    ['view', 'add_to_cart', 'remove_from_cart', 'add_to_cart', 'purchase'],
    # Pattern 4: Multiple views before action
    ['view', 'view', 'add_to_cart', 'purchase'],
    # Pattern 5: Browse and review
    ['view', 'rate_review', 'share'],
    # Pattern 6: Wishlist flow
    ['view', 'add_to_wishlist', 'view', 'add_to_cart', 'purchase'],
]

def generate_sequential_data(num_samples, num_users, num_products):
    """Generate data with realistic user behavior sequences."""
    data = []
    base_time = datetime(2026, 1, 1, 0, 0, 0)
    event_counter = 1

    # Generate data for each user with sequential patterns
    samples_per_user = num_samples // num_users
    extra_samples = num_samples % num_users

    for user_idx in range(1, num_users + 1):
        num_user_samples = samples_per_user + (1 if user_idx <= extra_samples else 0)
        user_time = base_time + timedelta(days=random.randint(0, 30))

        # Randomly select a behavior pattern for this user session
        pattern = random.choice(BEHAVIOR_PATTERNS)
        pattern_idx = 0

        for _ in range(num_user_samples):
            # Get action from pattern or fall back to weighted random
            if pattern_idx < len(pattern):
                action = pattern[pattern_idx]
                pattern_idx += 1
            else:
                action = weighted_choice(ACTIONS, action_weights)

            product_id = random.choice(product_ids)
            context = generate_context(action)
            timestamp = generate_timestamp(user_time, random.randint(0, 86400))

            data.append({
                'event_id': f"evt_{event_counter:06d}",
                'user_id': user_idx,
                'product_id': product_id,
                'action': action,
                'context': context,
                'timestamp': timestamp,
            })

            event_counter += 1

        # Reset pattern for next user
        pattern_idx = 0

    # Shuffle to mix user sessions
    random.shuffle(data)
    return data

def main():
    print("Generating user behavior data...")
    data = generate_sequential_data(NUM_SAMPLES, NUM_USERS, NUM_PRODUCTS)

    with open('user_data.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['event_id', 'user_id', 'product_id', 'action', 'context', 'timestamp'])

        for row in data:
            writer.writerow([
                row['event_id'],
                row['user_id'],
                row['product_id'],
                row['action'],
                row['context'],
                row['timestamp']
            ])

    print(f"Generated {NUM_SAMPLES} samples in user_data.csv")

    # Print statistics
    action_counts = {a: 0 for a in ACTIONS}
    context_counts = {c: 0 for c in CONTEXTS}

    with open('user_data.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            action_counts[row['action']] = action_counts.get(row['action'], 0) + 1
            context_counts[row['context']] = context_counts.get(row['context'], 0) + 1

    print("\nAction distribution:")
    for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
        print(f"  {action}: {count} ({count/NUM_SAMPLES*100:.1f}%)")

    print("\nContext distribution:")
    for context, count in sorted(context_counts.items(), key=lambda x: -x[1]):
        print(f"  {context}: {count} ({count/NUM_SAMPLES*100:.1f}%)")

if __name__ == '__main__':
    main()
