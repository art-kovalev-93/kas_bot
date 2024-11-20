import time
import pyfiglet
from mexc_api.spot import Spot
from mexc_api.common.enums import OrderType, Side
from mexc_api.common.enums import Interval

def main():
    # Создаем объект figlet
    figlet = pyfiglet.Figlet()

    # Генерируем текст с приветствием
    greeting = figlet.renderText('H i,  A r t e m !')

    # Выводим приветствие
    print(greeting)

if __name__ == '__main__':
    main()

client = Spot(api_key="api_key", api_secret="api_secret")

def check_deposit():
    try:
        acc_info = client.account.get_account_info()
        for balance in acc_info.get('balances'):
            if balance.get('asset')=='USDT':
                free_usdt=balance.get('free')
                break
        print(f"Доступно USDT для покупки: {free_usdt}")
        return free_usdt
    except Exception:
        print("Ошибка при проверке депозита")
    #метод возвращает доступный баланс

price_start=0.177 #программа начнет работать когда текущая цена опустится до данного значения
sum_buy=int(float(check_deposit())//5) #программа будет покупать на данную часть от депозита, вместо 5 можно выставить любое другое число (или вообще написать sum_buy=100 тогда покупка будет каждый раз на 100$)
sl=0.15 #установите стоп лосс, программа прекратит закупать крипту если цена упадет, если вы хотите чтобы программа не только остановилась но и продала сразу всю Каспу по текущей цене то на строках 209 и 210 нужно удалить символ решетки вначале
tp=0.2 #по достижению этой цены программа начнет скальпить по чуть чуть вверх, как только после достижения пика она вернется к tp, программа завершится и зафиксирует прибыль

def get_time(): #время сервера
    time = client.market.server_time()
    return time

last_buy_time = get_time()
open_orders=client.account.get_open_orders("KASUSDT")
last_autosell_id=''
auto_order=True
last_buy_price=100000.0
last_qty_btc=''
trades=[]
rocket = False

def get_open_orders():
    try:
        #метод запрашивает открытые заказы
        open_orders=client.account.get_open_orders("KASUSDT")
        return open_orders
    except Exception as e:
        print(f'Ошибка при запросе открытых заказов: {e}')

def get_last_trade(): #метод возвращает последнюю покупку\продажу если возвращает isBuyer True - то последняя была покупка
    trades = client.account.get_trades("KASUSDT", limit='40')
    return trades[0] if trades else None  # Проверка на наличие трейдов

def autobuy_order():
    try:
        sum_buy = int(float(check_deposit()) // 5)
        client.account.new_order(symbol="KASUSDT", side=Side.BUY, order_type=OrderType.MARKET, quote_order_quantity=sum_buy) #сделали покупку
        global last_autosell_id, last_buy_price, last_qty_btc  # Добавлено для глобальной видимости
        last_buy_price=float(last_buying_price()) #записали последнюю цену покупки
        trades = client.account.get_trades("KASUSDT", limit='40')
        for trade in trades:
            if trade.get('isBuyer'):
                qty = float(trade.get('qty'))
                break
        return print(f'Купили {qty} KAS по цене {last_buy_price}')
    except Exception as e:
        print(f'Ошибка при покупке ордера: {e}')

def is_autobuy_sold(last_autosell_id):
    open_orders=client.account.get_open_orders("KASUSDT")
    for open_order in open_orders:
        if last_autosell_id == open_order.get('orderId'):
            return False
            break
    return True

#quantity количество битка
#quote_order_quantity количество usdt

def sell():
    price_sell=str(last_buying_price()*1.005)
    qty = free_btc()
    client.account.new_order(symbol="KASUSDT", side=Side.SELL, order_type=OrderType.LIMIT, price=price_sell, quantity=qty)
    return print(f'Выставили на продажу {qty} KAS по цене {price_sell}')

def free_btc():
    acc_info = client.account.get_account_info()
    coins = acc_info.get("balances")
    for coin in coins:
        if coin.get('asset') == 'KAS':
            return float(coin.get('free')) #возвращаем кол-во биткоинов которые можем продать

def last_buying_price():
    trades = client.account.get_trades("KASUSDT", limit='20')
    for trade in trades:
        if trade.get('isBuyer'):
            last_buy_price = float(trade.get('price'))
            return last_buy_price
            break

def last_sell_price():
    trades = client.account.get_trades("KASUSDT", limit='50')
    for trade in trades:
        if not trade.get('isBuyer'):
            last_sell_price = float(trade.get('price'))
            return last_sell_price
            break

def get_current_price():
    try:
        current_price_info=client.market.ticker_price('KASUSDT')
        btc_obj=current_price_info[0]
        current_price=float(btc_obj.get('price'))
        return current_price
    except Exception as e:
        print(f'Ошибка при запросе текущей цены: {e}')

def get_klines():
    obj=client.market.klines('KASUSDT',interval=Interval.ONE_MIN,limit=6,start_ms=0)
    return obj


def is_go_up(avg_ma_t):
    cur_pr=get_current_price()
    if avg_ma_t>cur_pr:
        print(f'график идет вниз, ждем. средняя цена: {avg_ma_t}, текущая цена: {cur_pr}')
        return False
    else:
        print(f'график идет вверх, покупаем. средняя цена: {avg_ma_t}, текущая цена: {cur_pr}')
        return True

while True:
    if get_current_price()<=price_start:
        while True:
            try:
                if float(check_deposit())>sum_buy:
                    number_of_orders=len(get_open_orders())
                    if number_of_orders<51:
                        if number_of_orders>0:
                            open_orders = client.account.get_open_orders("KASUSDT")
                            for open_order in open_orders:
                                if last_autosell_id == open_order.get('orderId'):
                                    auto_order = False
                                    break
                                else:
                                    auto_order = True
                            if auto_order:
                                print("Автобай продан, делаем новый")
                                autobuy_order()
                                sell()
                                open_orders = client.account.get_open_orders("KASUSDT")
                                last_autosell_id=open_orders[0].get('orderId')  # записали id
                                last_buy_time = get_time()
                                time.sleep(5)
                            else:
                                print("Автобай не продан")
                                last_price = last_buying_price()
                                print(f'цена последней покупки {last_price}')
                                btc_price = get_current_price()
                                print(f'цена крипты {btc_price}')
                                if btc_price<last_price*0.995:
                                    autobuy_order()
                                    sell()
                                    last_buy_time = get_time()
                                    time.sleep(5)
                                else:
                                    print('Цена изменилась не значительно, ждем.')
                                    server_time = get_time()
                                    time_spend = (server_time - last_buy_time) // 1000
                                    if int(time_spend) > 900 and float(check_deposit())>sum_buy*20:
                                        print('Прошло больше 150 мин без покупки и хватает на 20+ ордеров.')
                                        autobuy_order()
                                        sell()
                                        last_buy_time = get_time()
                                    time.sleep(5)
                        else:
                            print('Нет ордеров, делаем новый')
                            server_time = get_time()
                            time_spend = (server_time - last_buy_time) // 1000
                            if int(time_spend) <= 60:
                                print('Зеленая ракета!')
                                autobuy_order()
                                sell()
                            else:
                                autobuy_order()
                                sell()
                            last_autosell_id=open_orders[0].get('orderId')  # записали id
                            last_buy_time = get_time()
                            time.sleep(5)
                    else:
                        print(f'открыто 50 ордеров, ждем продажи, инвестор')
                        time.sleep(5)
                else:
                    print(f'Ты инвестор, не хватает денег для ордера')
                    time.sleep(5)
            except Exception as e:
                print(f'Произошла ошибка: {e}')
                time.sleep(5)
            if get_current_price()<sl and rocket == False:
                print('Stop loss')
                #client.account.cancel_open_orders('KASUSDT')
                #client.account.new_order(symbol="KASUSDT", side=Side.SELL, order_type=OrderType.MARKET, quantity=free_btc())
                break
            elif get_current_price() < sl and rocket == True:
                print('Take profit, фиксируем')
                client.account.cancel_open_orders('KASUSDT')
                client.account.new_order(symbol="KASUSDT", side=Side.SELL, order_type=OrderType.MARKET, quantity=free_btc())
                break
            elif get_current_price()>=tp:
                print('Take profit, меняем стоп лос')
                sl=tp-0.001
                rocket = True
        break
    else:
        print('Цена выше старта продаж')
        time.sleep(10)
