import csv
import sys

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} input.csv output.csv")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, mode="r", newline="", encoding="utf-8") as infile, \
     open(output_file, mode="w", newline="", encoding="utf-8") as outfile:

    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for row in reader:
        writer.writerow(row[1:])  # Skip first column

print(f"First column removed. Output saved to {output_file}")

