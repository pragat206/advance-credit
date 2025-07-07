import sys
from app.scrapers.tata_scraper import save_tata_loans
from app.scrapers.axis_scraper import save_axis_loans
from app.scrapers.icici_scraper import save_icici_loans

if __name__ == '__main__':
    print('Updating Tata Capital loan data...')
    save_tata_loans()
    print('Updating Axis Bank loan data...')
    save_axis_loans()
    print('Updating ICICI Bank loan data...')
    save_icici_loans()
    print('All partner loan data updated.') 