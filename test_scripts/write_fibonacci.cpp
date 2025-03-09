#include <iostream>
#include <vector>

using namespace std;

int main(int argc, char* argv[]){
  int n = atoi(argv[0]);
  vector<int> fibonacci_dp(n, 0);
  fibonacci_dp[1] = 1;

  for(int i=2; i<n; i++){
    fibonacci_dp[i] = fibonacci_dp[i-1] + fibonacci_dp[i-2];
  }

}