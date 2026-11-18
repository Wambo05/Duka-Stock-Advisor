#include <iostream>
#include <cstdlib>
#include <ctime>

using namespace std;

int main() {
    // Seed the random number generator
    srand(static_cast<unsigned int>(time(nullptr)));
    int secretNumber = rand() % 100 + 1;
    int guess = 0;
    int attempts = 0;

    cout << "=================================\n";
    cout << "   TERMUX NUMBER GUESSING GAME   \n";
    cout << "=================================\n";
    cout << "I have chosen a number between 1 and 100.\n";
    cout << "Can you guess what it is?\n\n";

    do {
        cout << "Enter your guess: ";
        if (!(cin >> guess)) {
            cout << "Invalid input. Please enter a number.\n";
            cin.clear();
            cin.ignore(10000, '\n');
            continue;
        }
        
        attempts++;

        if (guess > secretNumber) {
            cout << "Too high! Try a lower number.\n\n";
        } else if (guess < secretNumber) {
            cout << "Too low! Try a higher number.\n\n";
        } else {
            cout << "\n🎉 Congratulations! You found the number " << secretNumber;
            cout << " in " << attempts << " attempts!\n";
        }
    } while (guess != secretNumber);

    return 0;
}

