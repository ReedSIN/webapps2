from django.shortcuts import render
from django.core.urlresolvers import reverse

from generic.views import *
from elections.models import *


# Create your views here.

VALID_FACTORS = [
    'student'
]

def index(request):
    authenticate(request, VALID_FACTORS)

    # Check if there are any open elections
    open_elections = bool(Election.get_open())

    template_args = {
        'open_elections': open_elections,
    }

    return render(request, 'elections/index.html', template_args)




def vote(request):
    authenticate(request, VALID_FACTORS)

    open_elections = Election.get_open()

    if not bool(open_elections):
        # If there are no elections, return them back to the elections index
        template_args = {
            'title' : 'No open elections',
            'message' : 'Sorry, there are no open elections for which you canvote in.',
            'redirect' : reverse('elections.views.index')
        }
        return render(request, 'generic/alert-redirect.phtml',
                      template_args)

    user = request.user

    # Try to get the users ballots if they have already
    # voted.
    ballots = Ballot.objects.filter(voter = user,
                                    election__in = open_elections)

    votes = {}

    if ballots:
        for ballot in ballots:
            election = ballot.election
            votes[election.id] = ballot.to_dict()
            votes[election.id]["quorum"] = ballot.quorum


    template_args = {
        'votes' : votes,
        'open_elections': open_elections
    }

    return render(request, 'elections/vote.html', template_args)




def submit_vote(request):
    authenticate(request, VALID_FACTORS)
    
    d = request.POST

    return HttpResponse(str(d))

    open_elections = Election.get_open()

    for election in open_elections:
        # Get their old ballot or create a new ballot
        try:
            ballot = Ballot.objects.get(election = election,
                                        voter = request.user)
        except Ballot.DoesNotExist:
            ballot = Ballot.objects.create(election = election,
                                           voter = request.user)

        # First, check if they checked quorum
        quorum = ''
        ballot.quorum = True
        try:
            quorum = d['quorum-' + str(election.id)]
        except KeyError:
            ballot.quorum = True
        if quorum is 'noquorum':
            ballot.quorum = False

        # Now record their votes, but only if they can
        if ballot.quorum == True and quorum != 'quorum':
            ballot.votes = writeVotes(election, d)

        ballot.save()

    return render(request, 'elections/submitted_vote.html')


def writeVotes(election, d):
    '''Creates the string to save the votes for a given ballot and form
    response dictionary.'''
    # 1. Create an array of candidates and ranks
    votes = []
    for candidate in election.candidate_set.all():
        rank = d[str(election.id) + '-' + str(candidate.id)][0]
        votes.append([candidate, int(rank)])

        # 2. Sort the array by the rank of candidates
    def get_rank(vote):
        return vote[1]
    votes.sort(key = get_rank)

        # 3. Build up the string of candidate ids to be saved
    vote_string = ""
    for vote in votes:
        vote_string += str(votes.pop(0)[0].id)
        vote_string += ","

    return vote_string[0:-1] # remove last comma
