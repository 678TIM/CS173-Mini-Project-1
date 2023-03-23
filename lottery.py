import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        # storage
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(5),
            max_tickets = sp.nat(5),
            operator = sp.test_account("admin").address
        )

    @sp.entry_point
    def buy_ticket(self, num_tickets): # MODIFY THIS TO ENABLE SOMEONE TO BUY MULTIPLE TICKETS
        sp.set_type(num_tickets, sp.TNat)
        # assertions
        sp.verify(num_tickets > 0, "INVALID TICKET AMOUNT")
        sp.verify(sp.amount >= sp.mul(num_tickets, self.data.ticket_cost), "INVALID AMOUNT")
        sp.verify(self.data.tickets_available >= num_tickets, "NOT ENOUGH TICKETS AVAILABLE. TXN IS REVERTED.")
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")

        tickets = sp.local("tickets", num_tickets)
        
        sp.while tickets.value > 0:
            # storage changes
            self.data.players[sp.len(self.data.players)] = sp.sender
            self.data.tickets_available = sp.as_nat(self.data.tickets_available - 1)
            
            # return extra tez
            tickets.value = sp.as_nat(tickets.value - sp.nat(1))
        
        extra_amount = sp.amount - sp.mul(num_tickets, self.data.ticket_cost)
        sp.if extra_amount > sp.tez(0):
            sp.send(sp.sender, extra_amount)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)
        # assertions
        sp.verify(self.data.tickets_available == 0, "GAME IS STILL ON")
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORIZED")
        
        # generate winner index
        winner_index = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_index]
        
        # send reward
        sp.send(winner_address, sp.balance)
        
        # reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_ticket_stuff(self, new_ticket_cost, new_max_tickets):        
        # assertions
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORIZED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "GAME IS ONGOING")
    
        # change stuff
        self.data.ticket_cost = new_ticket_cost
        self.data.max_tickets = new_max_tickets
        self.data.tickets_available = new_max_tickets
        

@sp.add_test(name="main")
def test():
    scenario = sp.test_scenario()

    # test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    charles = sp.test_account("charles")
    david = sp.test_account("david")
    elise = sp.test_account("elise")

    # Contract instance
    lottery = Lottery()
    scenario += lottery
    scenario.h1("TEST #1")
    scenario.h2("Buying Multiple Tickets")
    # buy_ticket
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender=alice)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(2), sender=bob)
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(3), sender=charles, valid=False) # REVERTED CUZ WANTS TO BUY MORE THAN THE AVAILABLE NUM_TICKETS)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender=david)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender=elise)

    scenario.h2("Ending the Game")
    # end game
    scenario += lottery.end_game(25).run(now=sp.timestamp(23), sender=admin)

    scenario.h2("Transition to Test #2")
    # changing parameters
    scenario += lottery.change_ticket_stuff(new_ticket_cost = sp.tez(2), new_max_tickets = sp.nat(6)).run(sender=admin)

    scenario.h1("TEST #2")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(6), sender=alice)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(7), sender=bob)
    scenario += lottery.buy_ticket(3).run(amount = sp.tez(8), sender=charles)
    # NEXT 2 ARE REVERTED CUZ THEY WANT TO BUY MORE THAN THE AVAILABLE NUM_TICKETS)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(4), sender=david, valid=False)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(4), sender=elise, valid=False)
    # CAN'T END GAME CUZ NOT ADMIN
    scenario += lottery.end_game(25).run(now=sp.timestamp(23), sender=alice, valid=False)
    scenario += lottery.end_game(25).run(now=sp.timestamp(23), sender=admin)
    # CHANGES DENIED CUZ NOT ADMIN
    scenario += lottery.change_ticket_stuff(new_ticket_cost = sp.tez(5), new_max_tickets = sp.nat(10)).run(sender=alice, valid=False)
    scenario += lottery.change_ticket_stuff(new_ticket_cost = sp.tez(5), new_max_tickets = sp.nat(10)).run(sender=admin)