import csv
from operator import itemgetter

def get_upc_from_file(filename):
    with open(filename, mode='r') as infile:
        reader = csv.DictReader(infile)
        all_upc = [row for row in reader]
        return all_upc

def get_categories_from_file(filename):
    with open(filename, mode='r') as infile:
        reader = csv.DictReader(infile)
        categories = [row for row in reader]
        return categories

def fill_acceptable_rank(all_upc, categories):
    for item in all_upc:
        if item['group']:
            for cat in categories:
                if item['group'] in cat['category']:
                    item['acceptable_rank'] = cat['top5']
    return all_upc

def remove_filds_with_rank_greater_then_acceptable_rank(all_upc):
    items_for_delete = []
    for item in all_upc:
        if item['rank'] and item['acceptable_rank']:
            if int(item['rank'].replace(',', '')) > int(item['acceptable_rank']):
                items_for_delete.append(item)

    for item in items_for_delete:
        all_upc.remove(item)

    return all_upc

def fill_weight_cost(all_upc):
    for item in all_upc:
        if item['weight']:
            item['weight_cost'] = str(float(item['weight'].replace(',', '')) * 0.75)

    return all_upc

def fill_ROI(all_upc):
    for item in all_upc:
        if item['net_payout'] and item['weight_cost'] and item['cost']:
            item['ROI'] = \
                float(item['net_payout'].replace('$', '').replace(',', '')) - \
                (float(item['cost'].replace('$', '').replace(',', ''))*0.7) - \
                float(item['weight_cost'])

    return all_upc

def remove_negative_ROI(all_upc):
    items_for_delete = []
    for item in all_upc:
        if item['ROI'] < 0.0:
            items_for_delete.append(item)

    for item in items_for_delete:
        all_upc.remove(item)
    return all_upc

def sort_by_field(all_upc, field):
    return sorted(all_upc, key=itemgetter(field))

def save_to_file(filename, all_upc):
    keys = all_upc[0].keys()
    with open(filename, 'wb') as output_file:
        writer = csv.DictWriter(output_file, keys)
        writer.writeheader()
        writer.writerows(all_upc)


if __name__ == '__main__':
    for i in range(1, 4):
        all_upc = get_upc_from_file('walmart_products_%s_new.csv' % str(i))
        categories = get_categories_from_file('categories.csv')

        all_upc = fill_acceptable_rank(all_upc, categories)
        all_upc = remove_filds_with_rank_greater_then_acceptable_rank(all_upc)
        all_upc = fill_weight_cost(all_upc)
        all_upc = fill_ROI(all_upc)
        all_upc = remove_negative_ROI(all_upc)
        all_upc = sort_by_field(all_upc, 'ROI')

        save_to_file('walmart_new_%s.csv' % str(i), all_upc)
