def make_unique(values, delim='$|$|'):
    unique = set()
    output = []
    for val in values:
        curr_val = val
        while curr_val in unique:
            curr_val += delim
        unique.add(curr_val)
        output.append(curr_val)

    return output, delim
    


if __name__ == '__main__':
    print(make_unique(['a', 'a', 'a$', 'b', 'a$|$|']))
