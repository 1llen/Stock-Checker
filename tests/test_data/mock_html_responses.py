# Mock HTML responses for testing

MOCK_IN_STOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Product</title>
</head>
<body>
    <div class="product-content">
        <h1>Test Product Name</h1>
        <div class="product-form">
            <form method="post" action="/cart/add">
                <button type="submit" name="add" class="btn product-form__cart-submit" data-add-to-cart="">
                    <span data-add-to-cart-text="">
                        Add to cart
                    </span>
                    <span class="hide" data-loader="">
                        <svg aria-hidden="true" focusable="false" role="presentation" class="icon icon-spinner" viewBox="0 0 20 20">
                            <path d="M7.229 1.173a9.25 9.25 0 1 0 11.655 11.412 1.25 1.25 0 1 0-2.4-.698 6.75 6.75 0 1 1-8.506-8.329 1.25 1.25 0 1 0-.75-2.385z"></path>
                        </svg>
                    </span>
                </button>
            </form>
        </div>
    </div>
</body>
</html>
"""

MOCK_OUT_OF_STOCK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Product</title>
</head>
<body>
    <div class="product-content">
        <h1>Test Product Name</h1>
        <div class="product-form">
            <form method="post" action="/cart/add">
                <button type="submit" name="add" aria-disabled="true" class="btn product-form__cart-submit" data-add-to-cart="">
                    <span data-add-to-cart-text="">
                        Sold out
                    </span>
                    <span class="hide" data-loader="">
                        <svg aria-hidden="true" focusable="false" role="presentation" class="icon icon-spinner" viewBox="0 0 20 20">
                            <path d="M7.229 1.173a9.25 9.25 0 1 0 11.655 11.412 1.25 1.25 0 1 0-2.4-.698 6.75 6.75 0 1 1-8.506-8.329 1.25 1.25 0 1 0-.75-2.385z"></path>
                        </svg>
                    </span>
                </button>
            </form>
        </div>
    </div>
</body>
</html>
"""

MOCK_MULTIPLE_BUTTONS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Product</title>
</head>
<body>
    <div class="product-content">
        <h1>Test Product Name</h1>
        <div class="product-form">
            <form method="post" action="/cart/add">
                <button type="submit" name="notify" class="btn email-form__submit">
                    <span>Notify When Available</span>
                </button>
                <button type="submit" name="add" aria-disabled="true" class="btn product-form__cart-submit">
                    <span data-add-to-cart-text="">
                        Sold out
                    </span>
                </button>
            </form>
        </div>
    </div>
</body>
</html>
"""

MOCK_NO_BUTTON_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Product</title>
</head>
<body>
    <div class="product-content">
        <h1>Test Product Name</h1>
        <div class="product-form">
            <p>Product currently unavailable</p>
        </div>
    </div>
</body>
</html>
"""