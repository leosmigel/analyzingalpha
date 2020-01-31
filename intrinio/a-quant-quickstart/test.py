import backtrader as bt
 
if __name__ == '__main__':
    cerebro = bt.Cerebro()
 
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
 
    cerebro.run()
 
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
