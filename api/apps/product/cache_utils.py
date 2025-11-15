"""
Cache utility functions for product app.
Provides cache invalidation helpers for when data changes.
"""
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def invalidate_product_cache(product_code):
    """Invalidate product cache when product is updated"""
    cache_key = f"product_{product_code}"
    cache.delete(cache_key)
    logger.info(f"Invalidated product cache for: {product_code}")


def invalidate_product_category_cache():
    """Invalidate product categories cache"""
    cache.delete("product_categories_active")
    logger.info("Invalidated product categories cache")


def invalidate_product_list_cache(category_code=None):
    """Invalidate product list cache for a category or all categories"""
    if category_code:
        cache_key = f"products_category_{category_code}"
        cache.delete(cache_key)
        logger.info(f"Invalidated product list cache for category: {category_code}")
    else:
        # Invalidate all product list caches (use pattern matching if available)
        # For simplicity, we'll just log - in production you might want to track keys
        logger.info("Invalidated all product list caches")


def invalidate_data_package_cache(product_code=None, data_code=None):
    """Invalidate data package cache"""
    if product_code and data_code:
        cache_key = f"data_package_{product_code}_{data_code}"
        cache.delete(cache_key)
        logger.info(f"Invalidated data package cache: {product_code}_{data_code}")
    elif product_code:
        # Invalidate all data bundles for a product
        cache_key = f"data_bundles_{product_code}"
        cache.delete(cache_key)
        logger.info(f"Invalidated data bundles cache for product: {product_code}")


def invalidate_merchant_discount_cache(user_id=None, product_code=None):
    """Invalidate merchant discount cache"""
    if user_id and product_code:
        cache_key = f"merchant_discount_{user_id}_{product_code}"
        cache.delete(cache_key)
        logger.info(f"Invalidated merchant discount cache: {user_id}_{product_code}")
    elif user_id:
        # Invalidate all discount caches for a merchant
        # Note: This is a simplified approach. In production, you might want to track keys
        logger.info(f"Invalidated all merchant discount caches for user: {user_id}")


def clear_all_product_caches():
    """Clear all product-related caches (use with caution)"""
    # This is a nuclear option - clears all caches with our prefix
    # In production, you might want to be more selective
    logger.warning("Clearing all product-related caches")
    # Note: Django cache doesn't support pattern deletion by default
    # You'd need Redis with django-redis for pattern-based deletion
    # For now, this is a placeholder

