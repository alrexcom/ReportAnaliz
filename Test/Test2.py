def dec_fn(original_fn):  # это функция декоратор
    def wrap_fn(*args, **kwargs):
        print("action before:", original_fn.__name__)
        result = original_fn(*args, **kwargs)
        print("action after:", original_fn.__name__)
        return result

    return wrap_fn


@dec_fn  # указываем используемый декоратор
def my_fn(a, b):
    return (a, b)


res = my_fn(10, 20)

print(res)
# action before: my_fn
# action after: my_fn
# (10, 20)